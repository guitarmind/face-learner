#!/usr/bin/env python2

import sys
import argparse
import cv2
import face_processing as fp

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory
from twisted.python import log
from twisted.internet import reactor

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="localhost",
                    help='Websocket server hostname')
parser.add_argument('--port', type=int, default=9000,
                    help='Websocket server port')
parser.add_argument('--endpoint', type=str, default="ws://127.0.0.1:9000",
                    help='Websocket endpoint to upload images (ws:// or wss://)')
args = parser.parse_args()

# Capture from camera at location 0
cap = cv2.VideoCapture(0)

class WebcamClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection opened.")

        def hello():
            self.sendMessage(u"Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.reactor.callLater(1, hello)

        # start sending messages every second ..
        self.upload_image()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def upload_image(self):
        # Capture new frame
        ret, frame = cap.read()
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        width = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        print("Height: ", height)
        print("Width: ", width)

        data_url = fp.rgbframe_to_data_url(frame)
        msg = {
            "type": "IMAGE",
            "data_url": data_url
        }
        self.sendMessage(msg)

        # send every 500ms
        self.factory.reactor.callLater(0.5, self.upload_image)

def main(argv):
    log.startLogging(sys.stdout)

    factory = WebSocketClientFactory(args.endpoint)
    factory.protocol = WebcamClientProtocol

    reactor.connectTCP(args.host, args.port, factory)
    reactor.run()

    # When everything done, release the capture
    cap.release()

if __name__ == '__main__':
    main(sys.argv)
