# Project_Bee 🐝

[![GitHub license](https://img.shields.io/github/license/LygutaKsusha/Project_Bee)](

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


