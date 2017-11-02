#!/usr/bin/env python2

import sys
import argparse
import cv2
import json
import os
import random
import time
import uuid
import requests

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor, ssl
from threading import Thread

import face_processing as fp
import tts


parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="imwy.apps.exosite.io",
                    help='Websocket server hostname')
parser.add_argument('--port', type=int, default=443,
                    help='Websocket server port')
parser.add_argument('--endpoint', type=str, default="/webcam",
                    help='Websocket endpoint to upload images (ws:// or wss://)')
args = parser.parse_args()

# Capture frequency
cap_freq = 0.5

# Customize camera resolution
enable_resize = True
cap_width = 400
cap_height = 300
# cap_width = 320
# cap_height = 240

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()

camera.brightness = 70
camera.sharpness = 0
camera.contrast = 0
camera.brightness = 50
camera.saturation = 0
camera.ISO = 0
camera.video_stabilization = False
camera.exposure_compensation = 0
camera.exposure_mode = 'auto'
camera.meter_mode = 'average'
camera.awb_mode = 'auto'
camera.image_effect = 'none'
camera.color_effects = None
camera.rotation = 0
camera.hflip = False
camera.vflip = False
camera.crop = (0.0, 0.0, 1.0, 1.0)

camera.resolution = (640, 480)
rawCapture = PiRGBArray(camera, size=(640, 480))

# allow the camera to warmup
time.sleep(0.1)


class WebcamClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print(response)
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        self.pingsReceived = 0
        self.pongsSent = 0
        print("WebSocket connection opened.")

        # Start to upload images
        print("Start uploading Webcam snapshots ...")
        self.upload_image()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {} (code: {})".format(reason, code))

    def onPing(self, payload):
        self.pingsReceived += 1
        print("Ping received from {} - {}".format(self.peer, self.pingsReceived))
        self.sendPong(payload)
        self.pongsSent += 1
        print("Pong sent to {} - {}".format(self.peer, self.pongsSent))

    def upload_image(self):

        # Capture new frame with resize
        camera.capture(rawCapture, format="bgr")
        # camera.capture(rawCapture, format="bgr", resize=(cap_width, cap_height))
        frame = rawCapture.array

        print("Height: ", frame.shape[0])
        print("Width: ", frame.shape[1])

        if enable_resize:
            resized_frame = fp.resize_rgbframe(frame, cap_width, cap_height)
            print("Height: ", resized_frame.shape[0])
            print("Width: ", resized_frame.shape[1])
            frame = resized_frame

        timestamp = time.time()
        data_url = fp.rgbframe_to_data_url(frame)
        msg = {
            'capture_time': timestamp,
            'data_url': data_url
        }
        json_string = json.dumps(msg)
        self.sendMessage(json_string)

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

        # send every cap_freq second
        self.factory.reactor.callLater(cap_freq, self.upload_image)

def main(argv):
    log.startLogging(sys.stdout)

    ws_endpoint = "wss://{}{}".format(args.host, args.endpoint)
    factory = WebSocketClientFactory(ws_endpoint)
    factory.protocol = WebcamClientProtocol

    # SSL client context: default
    if factory.isSecure:
        contextFactory = ssl.ClientContextFactory()
    else:
        contextFactory = None

    connectWS(factory, contextFactory)
    reactor.run()

    # When everything done, release the capture
    camera.close()

if __name__ == '__main__':
    main(sys.argv)
