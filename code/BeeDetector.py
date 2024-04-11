##
# @file BeeDetector.py
# @brief Process that runs the neural network for bee image classification

from Utils import get_config
from os import listdir, makedirs
from os.path import isfile, join, exists
from datetime import datetime
import cv2
import time
import queue
import multiprocessing
import cv2
import logging
import numpy as np
import math
from Utils import get_config

logger = logging.getLogger(__name__)


class BeeProcess(object):
    def __init__(self):
        """! Initializes the defaults
        """
        self._stopped = multiprocessing.Value('i', 0)
        self._done = multiprocessing.Value('i', 0)
        self._process = None
        self._process_params = {}
        self._parentclass = self.__class__
        self._started = False

    def set_process_param(self, name, queue):
        self._process_params[name] = queue

    def isDone(self):
        return self._done.value

    def isStarted(self):
        return self._started

    def stop(self):
        """! Forces the process to stop
        """

        # Wait for process to stop

        self._stopped.value = 1
        for i in range(100):
            if self._done.value == 1:
                break
            time.sleep(0.01)
        if self._done.value == 0:
            logger.warning("Terminating process after waiting for gracefully shutdown!")
            self._process.terminate()

        for qn, q in self._process_params.items():
            if q is not None:
                try:
                    while not q.empty():
                        q.get()
                except:
                    pass

    def join(self):
        if self._stopped.value == 0 and self._done.value == 0 and self._started:
            self._process.join()

    @staticmethod
    def run(*args):
        print("run")
        time.sleep(1)

    @staticmethod
    def _run(args):

        parent = args["parent"]
        stopped = args["stopped"]
        done = args["done"]
        try:
            parent.run(**args)
        except KeyboardInterrupt as ki:
            logger.debug(">> Received KeyboardInterrupt")

        stopped.value = 1
        done.value = 1

    def start(self):
        """! Starts the image extraction process
        """
        # Start the process
        args = self._process_params.copy()
        args["parent"] = self._parentclass
        args["stopped"] = self._stopped
        args["done"] = self._done

        self._process = multiprocessing.Process(target=self._run, \
                                                args=[args])
        self._process.start()
        self._started = True

class BeeClassification(BeeProcess):
    """! The 'BeeClassification' class provides access to the neural network
          that runs as a separate process. It provides two queue-objects,
          one to queue to incoming images that have to be processed by the
          neural network and a second one, where the results are put.
    """

    def __init__(self):

        """! Initializes the neural network and the queues
        """
        super().__init__()

        # reports when the porcess with the neural network is ready
        self._ready = multiprocessing.Value('i', 0)
        self.set_process_param("ready", self._ready)

        # The queue for the incoming images
        self._q_in = multiprocessing.Queue(maxsize=20)
        self.set_process_param("q_in", self._q_in)

        ## The queue where the results are reported
        self._q_out = multiprocessing.Queue()
        self.set_process_param("q_out", self._q_out)

        # Start the process and wait for it to run
        self.start()
        while self._ready.value == 0:
            time.sleep(5)
            logger.info("Waiting for neural network, may take 1-2 minutes")
        logger.debug("Classification terminated")

    def getQueue(self):
        """! Returns the queue-object for the incoming queue
        @return  Returns the incoming queue object
        """
        return self._q_in

    def getResultQueue(self):
        """! Returns the queue-object which holds the classification results
        @return  Returns the result queue object
        """
        return self._q_out

    @staticmethod
    def run(q_in, q_out, ready, parent, stopped, done):
        """! Static method, starts a new process that runs the neural network
        """

        # Include tensorflow within the process
        import tensorflow as tf

        _process_time = 0
        _process_cnt = 0

        # Enable growth of GPU usage
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        config.gpu_options.per_process_gpu_memory_fraction = 0.75  # added to limit GPU memory usage
        session = tf.compat.v1.InteractiveSession(config=config)

        # Load the model
        try:
            _model = tf.keras.models.load_model(get_config("NN_MODEL_FOLDER"))
            _model.trainable = False
        except Exception as e:
            ready.value = True
            logger.error("Failed to load Model: %s" % (e,))
            return


        # Detect desired image size for classification
        img_height = 300
        img_width = 150
        if get_config("NN_CLASSIFY_RESOLUTION") == "EXT_RES_75x150":
            img_height = 150
            img_width = 75

        # Initialize the network by using it
        if True:

            # Load all images from the "Images" folder and feed them to the neural network
            # This ensures that the network is fully running when we start other processes
            test_images = ["Images/"+f for f in listdir("Images") if isfile(join("Images", f))]
            imgs = []
            for item in test_images:
                img = tf.io.read_file(item)
                img = tf.image.decode_jpeg(img, channels=3)
                img = tf.image.resize(img, [img_height, img_width])
                imgs.append(img)

            # Perform prediction
            _model.predict_on_batch(tf.convert_to_tensor(imgs))

        # Mark process as ready
        ready.value = True

        # Create folders to store images with positive results
        if get_config("SAVE_DETECTION_IMAGES"):
            for lbl in ["varroa"]:
                s_path = get_config("SAVE_DETECTION_PATH")
                if not exists(join(s_path, lbl)):
                    makedirs(join(s_path, lbl))

        classify_thres = get_config("CLASSIFICATION_THRESHOLDS")
        while stopped.value == 0:

            # While the image classification queue is not empty
            # feed the images to the network and push the result
            # back in the outgoing queue
            if not q_in.empty():
                _start_t = time.time()
                _process_cnt += 1

                images = []
                images_orig = []
                tracks = []

                # Load the images from the in-queue and prepare them for the use in the network
                failed = False
                while len(images) < 5 and stopped.value == 0:
                    try:
                        item = q_in.get(block=False)
                    except queue.Empty:
                        item = None
                        break

                    if not item is None:
                        t, img, frame_id = item
                        images_orig.append(img)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        if img.shape != (img_height, img_width, 3):
                            img = tf.image.resize(img, [img_height, img_width])
                        images.append(img)
                        tracks.append((t, frame_id))

                # Quit process if requested
                if stopped.value != 0:
                    return

                # Feed collected images to the network
                if len(tracks):
                    results = _model.predict_on_batch(tf.convert_to_tensor(images))

                    # precess results
                    for num, t_data in enumerate(tracks):

                        track, frame_id = t_data

                        # Create dict with results
                        entry = set([])
                        for lbl_id, lbl in enumerate(["varroa"]):
                            if results[lbl_id][num][0] > classify_thres[lbl]:
                                entry.add(lbl)

                                # Save the corresponding image on disc
                                if get_config("SAVE_DETECTION_IMAGES") and lbl in get_config("SAVE_DETECTION_TYPES"):

                                    img = images_orig[num]
                                    cv2.imwrite(get_config("SAVE_DETECTION_PATH") + "/%s/%i-%s-%i.jpeg" % (lbl, _process_cnt, \
                                            datetime.now().strftime("%Y%m%d-%H%M%S"), frame_id), img)

                        # Push results back
                        q_out.put((tracks[num][0], entry))

                _end_t = time.time() - _start_t
                logger.debug("Process time: %0.3fms - Queued: %i, processed %i" % (_end_t * 1000.0, q_in.qsize(), len(images)))
                _process_time += _end_t
            else:
                time.sleep(0.5)
        logger.info("Classification stopped")


def detect_bees(frame, scale):

    # Helper method to calculate distance between ellipses
    def near(p1,p2):
        return math.sqrt(math.pow(p1[0]-p2[0], 2) + math.pow(p1[1]-p2[1], 2))

    # Helper method to calculate the area of an ellipse
    def area(e1):
        return np.pi * e1[1][0] * e1[1][1]

    b,g,r = cv2.split(frame)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)

    o = 255 - (g - v)

    # Blur Image and perform a binary thresholding
    o = cv2.GaussianBlur(o, (9,9), 9)
    _, o = cv2.threshold(o, get_config("BINARY_THRESHOLD_VALUE"), \
            get_config("BINARY_THRESHOLD_MAX"), cv2.THRESH_BINARY)

    # Invert result
    o = 255 -o

    # Detect contours
    contours, hierarchy = cv2.findContours(o, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)
    ellipses = []
    groups = []
    for i in range(len(contours)):

        if(len(contours[i]) >= 5):
            # Fit ellipse
            e = cv2.fitEllipse(contours[i])
            # Skip too small detections
            if e[1][0] < 8 or e[1][1] < 8:
                continue
            # Only use ellipses with minium size
            ellipseArea = area(e)
            if ellipseArea > get_config("DETECT_ELLIPSE_AREA_MIN_SIZE") \
                    and ellipseArea < get_config("DETECT_ELLIPSE_AREA_MAX_SIZE"):

                # Scale ellipse to desired size
                e = ((e[0][0] * scale, e[0][1] * scale), (e[1][0] * scale, e[1][1] * scale), e[2])
                ellipses.append(e)
            elif ellipseArea > get_config("DETECT_GROUP_AREA_MIN_SIZE") and \
                    ellipseArea < get_config("DETECT_GROUP_AREA_MAX_SIZE"):

                # Scale ellipse to desired size
                e = ((e[0][0] * scale, e[0][1] * scale), (e[1][0] * scale, e[1][1] * scale), e[2])
                groups.append(e)

    # Merge nearby detection into one
    done = []
    skip = []
    solved = []
    for a in ellipses:

        # Find ellipses that are close to each other and store them as a group
        group = []
        for b in ellipses:

            # Skip self and already processed ellipses
            if (a,b) in done or (b,a) in done or a == b:
                continue
            done.append((a,b))
            dist = near(a[0],b[0])
            if dist < 50:

                # Put them into the group
                if a not in group:
                    group.append(a)
                if b not in group:
                    group.append(b)

                # Remember which ellipses were processed
                if not a in skip:
                    skip.append(a)
                if not b in skip:
                    skip.append(b)

        if len(group):
            solved.append(max(group, key=area))

    rest = list(filter(lambda x: x not in skip, ellipses))
    merged = rest + solved

    return merged, groups



