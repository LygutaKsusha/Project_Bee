# Project_Bee 🐝

A camera-based monitoring system that identifies and tracks bees (utilizes Tensorflow, Opencv and some others).


## Presentation

More information can be found in the [Presentation](https://github.com/LygutaKsusha/Project_Bee/blob/main/Presentation.pdf)


## Give it a go

Check out this repository and install the dependencies:

```
git clone https://github.com/LygutaKsusha/Project_Bee
cd Project_Bee/code
pip3 install -r requirements.txt
```

## How to use

All settings you may play around are defined in the 
[Config](https://github.com/LygutaKsusha/Project_Bee/blob/main/code/config.yaml) file

By setting relevant property to True/False will change workflow of the project
in the needed direction.

As for example - by setting USE_GSTREAM to True will enable camera tracks and it will
start process of streaming video. You can define where save video and then work with it
for further segmetaion, extracting photo, labeling and train your Model to recognize infections based on the gathered information.

All settings and properties can be changed/enabled/disabled in the 
[Config](https://github.com/LygutaKsusha/Project_Bee/blob/main/code/config.yaml) file

Each frame captured by the camera (or from a video file) will be processed to detect bees within the image. The positions of the bees identified will then be used to track their movements and paths using Kalman filters.

Once a bee is detected, it will be isolated from the image, rotated as necessary, and sent to a neural network for classification.

The neural network performs basic classification tasks to identify bees infected with Varroa mites. These results can also be visualized. The neural network operates independently, and its results might not be immediate enough to display in real-time, especially if the bee has moved out of the camera's view. This timing issue depends on the capabilities of the system being used.

The neural network was trained using data gathered from the mentioned camera system. So you might observe different outcomes due to variations in camera angles, resolutions, clarity, background color, and other factors. In such cases, you should create your own dataset and use it to train the neural network. 

Take to account that each environment is different so you'll get different results every time,
e.g. different video samples, so you would need to re-train your Model to keep better detecting while streaming on-line and trying analize on-the fly varroa infections.

So first you would need to train you Model based on the video gathered, and after that keep tracking 
on-line based on the prepared information.

Continues track can be set up by running script without any arguments in the background 

```
python3 main.py
```

For the demo purpose USE_GSTREAM was set to False. The model has been already trained based on some samples of the video. You can download example files here <a href="https://www.youtube.com/watch?v=xBye2Or-ptk">Sample Video</a> or here
<a href="https://www.youtube.com/watch?v=2bzwwklDFr0&t=24s">Sample Video 2</a>

So lets pretend that we are monitoring bhive on line, but our test environment will be sample of the video.

Start the monitoring system by calling script with argument:

```
python3 main.py --video=./VIDEO_FILE_NAME
```

This is what you should get:

 - Bees with Varroa mites in the video will be marked with Red dots

## Configuration

You can extend/modify parameters based on the needs in the [Config](https://github.com/LygutaKsusha/Project_Bee/blob/main/code/config.yaml) file.

## Discussion of improvement opportunities

As a further improvement, some pre-trained models could be taken to account that already have the capability and required functionality. Here are a few options:

1. YOLO (You Only Look Once): YOLO is a real-time object detection system that can identify objects in images and videos. It's fast and accurate, making it a good choice for tracking bees. There are several versions of YOLO available, including YOLOv3, YOLOv4, and YOLOv5. We can use a pre-trained YOLO model and fine-tune it on a dataset of bee images to improve its performance.

2. MobileNet-SSD: MobileNet-SSD is a lightweight object detection model that's designed to run on mobile devices. It's less accurate than YOLO, but it's faster and requires less computing power. We can use a pre-trained MobileNet-SSD model and fine-tune it on a dataset of bee images.

3. Faster R-CNN: Faster R-CNN is a state-of-the-art object detection model that's accurate and fast. It's more complex than YOLO and MobileNet-SSD, but it can achieve better results. We can use a pre-trained Faster R-CNN model and fine-tune it on a dataset of bee images.

Some more experiments are needed here with these models and parameters to find the most appropriate solution for the project.


