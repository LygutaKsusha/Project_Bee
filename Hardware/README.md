## Hardware Requirements

Some information can be also found in the [Presentation](https://github.com/LygutaKsusha/Project_Bee/blob/main/Presentation.pdf)




## How to connect

To connect a Raspberry Pi NoIR Camera Module v2 to an NVIDIA Jetson Nano and enable WiFi, follow these steps:

- Connect the Camera: Ensure the Jetson Nano is powered off and disconnected from any power source. Connect the camera's ribbon cable to the CSI port on the Jetson Nano. The silver side of the connector should face towards the board, and the blue side should face away from the board. This orientation is crucial for proper connection.

- Power On and Verify Connection: Power on the Jetson Nano and check if the camera is recognized. You can verify this by looking for a device file corresponding to the camera. If you don't see the device file, ensure the ribbon cable is correctly oriented and that you are using a Version 2 Pi camera, as Version 1 will not work.

- Test the Camera Stream: To test the camera stream, you can use the GStreamer command provided in the source. This command streams the camera output to the monitor, allowing you to visually confirm that the camera is functioning correctly with the Jetson Nano. The command is as follows:

```
gst-launch-1.0 nvarguscamerasrc! 'video/x-raw(memory:NVMM),width=3820, height=2464, framerate=21/1
```
This command uses GStreamer to capture video from the camera, processes it, and displays it on the screen.

- Enable WiFi: To enable WiFi on the Jetson Nano, you can use the nmtui command-line utility. This tool provides a text-based interface for managing network connections. Simply open a terminal and type nmtui. Follow the prompts to set up a WiFi connection. You will need to enter your network's SSID and password.

Raspberry in our case will be as remote server that you can connect remotly. 

- Consider to use LXDE as your desktop environment. All detailed instructions can be found here -
https://jetsonhacks.com/2020/11/07/save-1gb-of-memory-use-lxde-on-your-jetson/

- Configuring VNC for LXDE

It is also possible to use LXDE when you do Remote Desktop to your Jetson Nano. It is enough to update xstartup file in ~/.vnc by commenting /etc/X11/Xsession and adding /usr/bin/startlxde

```
xrdb $HOME/.Xresources xsetroot -solid grey -terminal-emulator -geometry 80x24+10+10 -ls -title “$VNCDESKTOP Desktop” & # Fix to make GNOME work export XKL_XMODMAP_DISABLE=1 #/etc/X11/Xsession /usr/bin/startlxde
```

## Discussion of improvement opportunities

Taking to account the cost of the hardware (NVDIDIA Jetson Eveloper Kit is not of the cheapest ones), might be considered to use some Raspberry Pi models for the project. It will be more cost-effective and will be able to handle the project requirements as well.

For example - Raspberry Pi 4 Model B (4GB RAM): This is a powerful and affordable single-board computer that can handle computer vision tasks. It's not as powerful as the NVIDIA Jetson, but it's a good budget option. It has a quad-core Cortex-A72 CPU running at 1.5GHz, 4GB of LPDDR4 RAM, and Gigabit Ethernet, among other features.

It would work in conjunction with the Raspberry Pi High Quality Camera: this is a higher resolution camera than the Camera Module 2, with a 12.3 megapixel Sony IMX477 sensor. It's compatible with the Raspberry Pi 4 and can be used with a C-Mount lens for better focus on the bees.

Some thoughts and concerns could be around the power consumption, as the Raspberry Pi might consume more power than the Jetson (that's why Jetson has been chosen as the first option).

Additionally to this you also would need A CSI camera cable (included with the High Quality Camera), a C-Mount lens (not included with the camera), and a power supply for the Raspberry Pi.

It's possible to connect to your Raspberry Pi remotely using a Remote Desktop Protocol (RDP). Initially you just would need to enable VNC Server on the App by itself and install a VNC Client on your PC.


## More and more info for curious

https://dmccreary.medium.com/getting-your-camera-working-on-the-nvida-nano-336b9ecfed3a 
https://jetsonhacks.com/2019/04/02/jetson-nano-raspberry-pi-camera/
https://www.zaferarican.com/post/how-to-save-1gb-memory-on-jetson-nano-by-installing-lubuntu-desktop
