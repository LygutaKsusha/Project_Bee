"""! @brief This module contains the 'ImageConsumer', which processes the video frames. """
##
# @file ImageProcessing.py
#
# @brief This module contains the 'ImageConsumer', which processes the video frames.


from pathlib import Path

from Utils import cutEllipseFromImage, get_config, get_frame_config
import datetime
from os.path import join, exists
from os import makedirs
import cv2
import time
import logging
import queue
import multiprocessing
from Statistic import getStatistics
from BeeDetector import detect_bees
from BeeTracking import BeeTracker, BeeTrack
from Utils import get_config, get_args
from BeeDetector import BeeProcess
if get_config("NN_ENABLE"):
    from BeeDetector import BeeClassification

from multiprocessing import Queue

logger = logging.getLogger(__name__)

class ImageConsumer(BeeProcess):
    """! The 'ImageConsumer' processes the frames which are provided
    by the 'ImageProvider'. It performs the bee detection, bee tracking and
    forwards findings to the 'ImageExtractor' to feed them to the neural network.
    """
    def __init__(self):
        """! Intitilizes the 'ImageConsumer'
        """
        super().__init__()
        self._extractQueue = Queue()
        self._classifierResultQueue = None
        self._imageQueue = None
        self._visualQueue = None
        self.set_process_param("e_q", self._extractQueue)
        self.set_process_param("c_q", self._classifierResultQueue)
        self.set_process_param("i_q", self._imageQueue)
        self.set_process_param("v_q", self._visualQueue)

    def getPositionQueue(self):
        """! Returns the queue object where detected bee positions will be put
        @return A queue object
        """
        return self._extractQueue

    def setImageQueue(self, queue):
        """! Set the queue object where the image consumer can find new frames
        @param queue    The queue object to read new frames from
        """
        self._imageQueue = queue
        self.set_process_param("i_q", self._imageQueue)
    
    def setVisualQueue(self, queue):
        """! Set the queue object where the image consumer can find new frames
        @param queue    The queue object to read new frames from
        """
        self._visualQueue = queue
        self.set_process_param("v_q", self._visualQueue)

    def setClassifierResultQueue(self, queue):
        """! Set the queue obejct where the 'ImageConsumer' can read classification results
        @param  queue   The queue that provides the classification results from the neural network
        """
        self._classifierResultQueue = queue
        self.set_process_param("c_q", self._classifierResultQueue)

    @staticmethod
    def run(c_q, i_q, e_q, v_q, parent, stopped, done):
        """! The main thread that runs the 'ImageConsumer'
        """
        _process_time = time.time()
        _process_cnt = 0
        _lastProcessFPS = 0
        _start_t = time.time()
        writer = None

        # Create a Bee Tracker
        tracker = BeeTracker(50, 20)

        # Create statistics object
        statistics = getStatistics()

        if type(i_q) == type(None):
            raise("No image queue provided!")

        while stopped.value == 0:

            _process_cnt += 1

            # When the neural network is enabled, then read results from the classifcation queue
            # and forward them the the corresponding track and statistics
            if get_config("NN_ENABLE"):

                # Populate classification results
                while not c_q.empty():

                    # Transfer results to the track
                    trackId, result = c_q.get()
                    track = tracker.getTrackById(trackId)
                    if type(track) != type(None):
                        track.imageClassificationComplete(result)
                    else:
                        statistics.addClassificationResult(trackId, result)

            # Process every incoming image
            if not i_q.empty() and stopped.value == 0:

                if _process_cnt % 100 == 0:
                    logger.debug("Process time(get): %0.3fms" % ((time.time() - _start_t) * 1000.0))

                # Get frame set
                fs = i_q.get()
                if get_config("NN_EXTRACT_RESOLUTION") == "EXT_RES_150x300":
                    img_1080, img_540, img_180 = fs
                elif get_config("NN_EXTRACT_RESOLUTION") == "EXT_RES_75x150":
                    img_540, img_180 = fs
                
                if _process_cnt % 100 == 0:
                    logger.debug("Process time(track): %0.3fms" % ((time.time() - _start_t) * 1000.0))

                # Detect bees on smallest frame
                detected_bees, detected_bee_groups = detect_bees(img_180, 3)
                
                # Update tracker with detected bees
                if get_config("ENABLE_TRACKING"):
                    tracker.update(detected_bees, detected_bee_groups)

                # Extract detected bee images from the video, to use it our neural network
                # Scale is 2 because detection was made on img_540 but cutting is on img_1080
                if get_config("ENABLE_IMAGE_EXTRACTION"):
                    data = tracker.getLastBeePositions(get_config("EXTRACT_FAME_STEP"))
                    if len(data) and type(e_q) != type(None):
                        if get_config("NN_EXTRACT_RESOLUTION") == "EXT_RES_150x300":
                            e_q.put((data, img_1080, 2, _process_cnt))
                        elif get_config("NN_EXTRACT_RESOLUTION") == "EXT_RES_75x150":
                            e_q.put((data, img_540, 1, _process_cnt))
                        else:
                            raise("Unknown setting for EXT_RES_75x150, expected EXT_RES_150x300 or EXT_RES_75x150")

                # Draw the results if enabled
                if get_config("VISUALIZATION_ENABLED"):
                    if _process_cnt % get_config("VISUALIZATION_FRAME_SKIP") == 0:
                        try:
                            data = (img_540, detected_bees, detected_bee_groups, tracker, _lastProcessFPS) 
                            v_q.put(data, block=False)
                        except queue.Full:
                            print("frame skip !!")
                

                # Print log entry about process time each 100 frames
                if _process_cnt % 100 == 0:
                    _pt = time.time() - _process_time
                    _lastProcessFPS = 100 / _pt
                    logger.debug("Process time all: %0.3fms" % (_pt * 10.0))
                    _process_time = time.time()

                # Update statistics
                _dh = getStatistics()
                _dh.frameProcessed()

            else:
                time.sleep(0.01)

            # Limit FPS by delaying manually
            _end_t = time.time() - _start_t
            limit_time = 1 / get_config("LIMIT_FPS_TO")
            if _end_t < limit_time:
                time.sleep(limit_time - _end_t)
            _start_t = time.time()

        logger.info("Image Consumer stopped")


class ImageExtractor(BeeProcess):
    """! The 'ImageExtractor' class provides a process that extracts
          bee-images from a given video frame. It uses a queue for
          incoming requests, see 'setInQueue' and a one
          queue to provides results, see 'setResultQueue'.

          To request can be inserted in the incoming queue, by providing
          a tuple with the following contents:

            (data, image, scale)

          - 'data' contains the result of 'getLastBeePositions' from the 'BeeTracker'.
          - 'image' represents the frame to extract the bee images from.
          - 'scale' is used adapt to different frame sizes.
    """

    def __init__(self):
        """! Initializes the image extractor
        """
        super().__init__()
        self._resultQueue = None
        self._inQueue = None

    def start(self):
        """! Starts the image extraction process
        """
        if type(self._inQueue) == type(None):
            raise ("Please provide a classifier queue!")

        # Start the process
        super().start()

    def setResultQueue(self, queue):
        """! Sets the result queue of the image extractor
        @param queue  Sets the queue, where the process pushes its result
        """
        self._resultQueue = queue
        self.set_process_param("out_q", self._resultQueue)

    def setInQueue(self, queue):
        """! Sets the input queue of the image extractor
        @param queue  Sets the queue, where the process reads its input
        """
        self._inQueue = queue
        self.set_process_param("in_q", self._inQueue)

    @staticmethod
    def run(in_q, out_q, parent, stopped, done):

        """! Static method, starts the process of the image extractor
        """
        _process_time = 0
        _process_cnt = 0

        # Prepare save path
        e_path = get_config("SAVE_EXTRACTED_IMAGES_PATH")
        if get_config("SAVE_EXTRACTED_IMAGES") and not exists(e_path):
            makedirs(e_path)

        while stopped.value == 0:
            if not in_q.empty():

                _start_t = time.time()
                _process_cnt += 1

                # Read one entry from the process queue
                data, image, scale, frame_id = in_q.get()

                # Extract the bees from the image
                for item in data:
                    trackId, lastPosition = item

                    # Extract the bee image and sharpness value of the image
                    img, sharpness = cutEllipseFromImage(lastPosition, image, 0, scale)

                    # Check result, in some cases the result may be None
                    #  e.g. when the bee is close to the image border
                    if type(img) != type(None):

                        # Filter by minimum sharpness
                        if sharpness > get_config("EXTRACT_MIN_SHARPNESS"):

                            # Forward the image to the classification process (if its running)
                            if get_config("NN_ENABLE"):
                                try:
                                    out_q.put((trackId, img, frame_id), block=False)
                                except queue.Full:
                                    pass

                            # Save the image in case its requested
                            if get_config("SAVE_EXTRACTED_IMAGES"):
                                cv2.imwrite(e_path + "/%i-%s.jpeg" % (
                                _process_cnt, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")), img)

                _process_time += time.time() - _start_t

                # Print log entry about process time each 100 frames
                if _process_cnt % 100 == 0:
                    logger.debug("Process time: %0.3fms" % (_process_time * 10.0))
                    _process_time = 0

            else:
                time.sleep(0.01)

        # The process stopped
        logger.info("Image extractor stopped")

class ImageProvider(BeeProcess):

    """! The 'ImageProvider' class provides access to the camera or video
          input using a queue. It runs in a dedicated process and feeds
          the extracted images into a queue, that can then be used by other
          tasks.
    """
    def __init__(self, video_source=None, video_file=None):
        """! Initializes the image provider process and queue
        """
        super().__init__()

        self.frame_config = None
        self._videoStream = None

        # Validate the frame_config
        max_w = max_h = 0
        frame_config = get_frame_config()
        if not len(frame_config):
            raise BaseException("At least one frame config has to be provided!")

        # Ensure that each item of the frame config has the same size or less as the previous one
        for num, item in enumerate(frame_config):
            if type(item[0]) != int:
                raise BaseException("Expected item 1 of frame_config %i to be integer" % (num+1,))
            if type(item[1]) != int:
                raise BaseException("Expected item 2 of frame_config to be integer" % (num+1,))
            if item[2] not in (cv2.IMREAD_COLOR, cv2.IMREAD_GRAYSCALE, cv2.IMREAD_UNCHANGED):
                raise BaseException("Expected item 3 of frame_config to be one of cv2.IMREAD_COLOR, cv2.IMREAD_GRAYSCALE, cv2.IMREAD_UNCHANGED")

            if max_w < item[0]:
                max_w = item[0]
            if max_h < item[1]:
                max_h = item[1]

        # Ensure that at least one source is defined
        if video_source is None and video_file is None:
            raise BaseException("Either a video file or a video source id is required")

        # Prepare for reading from video file
        self.frame_config = frame_config
        if video_file is not None:
            self._queue = multiprocessing.Queue(maxsize=get_config("FRAME_SET_BUFFER_LENGTH_VIDEO"))
            vFile = Path(video_file)
            if not vFile.is_file():
                raise BaseException("The given file '%s' doesn't seem to be valid!" % (video_file,))
        else:
            self._queue = multiprocessing.Queue(maxsize=get_config("FRAME_SET_BUFFER_LENGTH_CAMERA"))

        self.set_process_param("video_file", video_file)
        self.set_process_param("video_source", video_source)
        self.set_process_param("config", self.frame_config)
        self.set_process_param("q_out", self._queue)
        self.start()

    def getQueue(self):
        """! Returns the queue-object where the extracted frames will be put.
        @return Returns the queue object
        """
        return self._queue

    @staticmethod
    def run(q_out, config, video_source, video_file, parent, stopped, done):

        # Open video stream
        if video_source == None:
            logger.info("Starting from video file input: %s" % (video_file,))
            # use HW acceleration for video file
            if get_config("USE_GSTREAM"):
                _videoStream = cv2.VideoCapture('filesrc location={}\
                                        ! queue ! h264parse ! omxh264dec ! nvvidconv \
                                        ! video/x-raw,format=BGRx,width=960,height=540 ! queue ! videoconvert ! queue \
                                        ! video/x-raw,format=BGR ! appsink'.format(video_file),
                                        cv2.CAP_GSTREAMER)
            else:
                _videoStream = cv2.VideoCapture(video_file)
        else:
            logger.info("Starting from camera input")
            _videoStream = cv2.VideoCapture(video_source)
            w, h, f = get_config("CAMERA_INPUT_RESOLUTION")
            if f != None:
                fourcc = cv2.VideoWriter_fourcc(*f)
                _videoStream.set(cv2.CAP_PROP_FOURCC, fourcc)
            if w != None:
                _videoStream.set(cv2.CAP_PROP_FRAME_WIDTH,  int(w))
            if h != None:
                _videoStream.set(cv2.CAP_PROP_FRAME_HEIGHT, int(h))

        _process_time = 0
        _process_cnt = 0
        _skipped_cnt = 0
        while stopped.value == 0:

            # Check if the queue is full
            if q_out.full():

                # If the queue is full, then report it
                if _skipped_cnt % 100 == 0:
                    logger.debug("Buffer reached %i" % (q_out.qsize(),))
                time.sleep(get_config("FRAME_SET_FULL_PAUSE_TIME"))
                _skipped_cnt += 1
            else:

                # There is still space in the queue, get a frame and process it
                _start_t = time.time()
                (_ret, _frame) = _videoStream.read()

                if _ret:

                    # Get the original shape
                    h, w, c = _frame.shape

                    # Convert the frame according to the given configuration.
                    # The image will be resized if necessary and converted into gray-scale
                    #  if needed.
                    fs = tuple()
                    for item in config:
                        width, height = _frame.shape[0:2]
                        if width != item[0] or height != item[1]:
                            _frame = cv2.resize(_frame, (item[1], item[0]))
                        if item[2] == cv2.IMREAD_GRAYSCALE:
                            tmp = cv2.cvtColor(_frame, cv2.COLOR_BGR2GRAY)
                            fs += (tmp,)
                        else:
                            fs += (_frame,)

                    # put the result in the outgoing queue
                    q_out.put(fs)

                    # Calculate the time needed to process the frame and print it
                    _process_time += time.time() - _start_t
                    _process_cnt += 1
                    if _process_cnt % 100 == 0:
                        logger.debug('FPS: %i (%i, %i)\t\t buffer size: %i' % (100/_process_time, w, h ,q_out.qsize()))
                        _process_time = 0
                else:
                    logger.error("No frame received!")
                    logger.error("> Try disabling USE_GSTREAM in the config.yaml!")
                    stopped.value = 1

        # End of process reached
        logger.info("Image provider stopped")
