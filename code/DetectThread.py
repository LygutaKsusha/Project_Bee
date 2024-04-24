# @file DetectThread.py
#
# @brief This module provides access to the WiFi network on NVIDIA Jetson.
import struct
from threading import Thread
import time
import logging
from Statistic import getStatistics
from Utils import get_config
import subprocess

logger = logging.getLogger(__name__)

class DetectThread(Thread):
    """! The WiFi object utilizes the nvnet utility for WiFi connectivity on NVIDIA Jetson.
         When initiated, this object runs in a separate thread.
    """

    def __init__(self):
        """Initializes the class"""
        self.stopped = False
        self._done = False
        self.wifi_enabled = get_config("WIFI_ENABLED")  # Check if WiFi is enabled in config
        Thread.__init__(self)

    def initialize_wifi(self):
        """Initializes the WiFi connection."""
        try:
            # Connect to WiFi network
            ssid = get_config("WIFI_SSID")
            password = get_config("WIFI_PASSWORD")
            subprocess.run(["sudo", "nvnet", "-s", ssid, "-p", password], check=True)
            logger.info("WiFi Connected.")
        except subprocess.CalledProcessError as e:
            logger.error("WiFi Connection failed: " + str(e))
            return False
        return True

    def send_data_over_wifi(self, data):
        """Sends data over the WiFi network."""
        if not self.initialize_wifi():
            return False

        try:
            # Placeholder for sending data over WiFi
            logger.info("Data sent over WiFi: %s" % data)
            return True
        except Exception as e:
            logger.error("Failed to send data over WiFi: %s" % str(e))
            return False

    def run(self):
        """Starts the WiFi thread."""
        if not self.wifi_enabled:
            logger.info("WiFi is disabled. Exiting WiFiSender.")
            return

        fail_cnt = 0
        while not self.stopped:
            # Get current statistics
            _dh = getStatistics()
            (_varroaCount, _beesIn, _beesOut, _frames) = _dh.readStatistics()

            # Reset statistics
            _dh.resetStatistics()

            # Prepare data
            data = (_varroaCount, _beesIn, _beesOut)
            data_bin = struct.pack("hhh", *data)

            # Convert monitoring results into a string
            data_bin_str = "".join("{:02X}".format(item) for item in data_bin)
            logger.debug("Binary data: %s" % str(data_bin))
            logger.debug("String data: %s" % data_bin_str)

            # Send data over WiFi
            if not self.send_data_over_wifi(data_bin_str):
                fail_cnt += 1

            # Wait for one minute before sending the next data
            time.sleep(60)

        # Thread stopped
        self._done = True
        logger.info("WiFi thread stopped.")

    def isDone(self):
        """Returns whether the Thread has stopped or is still running."""
        return self._done

    def stop(self):
        """Stops the WiFi Thread and joins it."""
        self.stopped = True
        self.join()