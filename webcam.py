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

# Capture from camera at location 0
cap = cv2.VideoCapture(0)

# Customize camera resolution
enable_resize = True
resize_width = 400
resize_height = 300
# resize_width = 320
# resize_height = 240

cap_width = 640
cap_height = 480
width_out = cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, cap_width)
height_out = cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, cap_height)


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

        # Capture new frame
        ret, frame = cap.read()
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        width = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        print("Height: ", height)
        print("Width: ", width)

        if enable_resize:
            resized_frame = fp.resize_rgbframe(frame, resize_width, resize_height)
            print("Height: ", resized_frame.shape)
            print("Width: ", resized_frame.shape)
            frame = resized_frame

        timestamp = time.time()
        data_url = fp.rgbframe_to_data_url(frame)
        data_url_size = round(sys.getsizeof(data_url) / 1000.0, 2)
        print("Image data url size: " + str(data_url_size) + " KB")
        msg = {
            'capture_time': timestamp,
            'data_url': data_url
        }
        json_string = json.dumps(msg)
        self.sendMessage(json_string)

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
    cap.release()

if __name__ == '__main__':
    main(sys.argv)
