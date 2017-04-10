#!/usr/bin/env python2

import sys
import argparse
import cv2
import json
import face_processing as fp

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor, ssl

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="markpeng-test01.apps.exosite.io",
                    help='Websocket server hostname')
parser.add_argument('--port', type=int, default=443,
                    help='Websocket server port')
parser.add_argument('--endpoint', type=str, default="wss://markpeng-test01.apps.exosite.io/webcam",
                    help='Websocket endpoint to upload images (ws:// or wss://)')
args = parser.parse_args()

# Capture from camera at location 0
cap = cv2.VideoCapture(0)
cap_width = 400
cap_height = 300

class WebcamClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print(response)
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection opened.")

        # self.sendHello()
        # start sending messages every second ..
        # self.upload_image()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        reactor.callLater(1, self.sendHello)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {} (code: {})".format(reason, code))

    def onPing(self, payload):
        self.pingsReceived += 1
        print("Ping received from {} - {}".format(self.peer, self.pingsReceived))
        self.sendPong(payload)
        self.pongsSent += 1
        print("Pong sent to {} - {}".format(self.peer, self.pongsSent))

    def sendHello(self):
        self.sendMessage(json.dumps({"test": "hello!"}))

    def upload_image(self):
        # Capture new frame
        ret, frame = cap.read()
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        width = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        print("Height: ", height)
        print("Width: ", width)
        resized_frame = fp.resize_rgbframe(frame, cap_width, cap_height)

        data_url = fp.rgbframe_to_data_url(resized_frame)
        msg = {
            "type": "IMAGE",
            "data_url": data_url
        }
        self.sendMessage(json.dumps(msg))

        # send every 500ms
        self.factory.reactor.callLater(0.5, self.upload_image)

def main(argv):
    log.startLogging(sys.stdout)

    headers = {'Origin': 'http://localhost/'}
    factory = WebSocketClientFactory(args.endpoint, headers=headers)
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
