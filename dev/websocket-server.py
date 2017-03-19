#!/usr/bin/env python2
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import txaio
txaio.use_twisted()

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from twisted.python import log
from twisted.internet import reactor

import argparse
import cv2
import json
from PIL import Image
import numpy as np
import os
import StringIO
import urllib
import base64
import time

import face_recognition

incoming_frame_width = 400
incoming_frame_height = 300
resize_ratio = 2

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=9000,
                    help='WebSocket Port')
args = parser.parse_args()

# Face object
class Face:
    def __init__(self, embeddings, labeled):
        self.embeddings = embeddings
        self.labeled = labeled

    def __repr__(self):
        return "{{labeled id: {}, embeddings[0:5]: {}}}".format(
            str(self.labeled),
            self.embeddings[0:5]
        )

class FaceLearnerProtocol(WebSocketServerProtocol):

    def __init__(self):
        # call init function of WebSocketServerProtocol
        super(self.__class__, self).__init__()
        self.images = {}

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        raw = payload.decode('utf8')
        msg = json.loads(raw)
        print("Received {} message of length {}.".format(
            msg['type'], len(raw)))
        if msg['type'] == "FRAME":
            start_time = time.time()
            content = self.processFrame(msg['dataURL'], msg['labeled'])
            msg = {
                "type": "ANNOTATED",
                "content": content,
                "processing_time": "{:.2f}".format(self.processing_time(start_time))
            }
            self.sendMessage(json.dumps(msg))
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def processFrame(self, dataURL, labled):
        start_time = time.time()
        head = "data:image/jpeg;base64,"
        assert(dataURL.startswith(head))
        imgdata = base64.b64decode(dataURL[len(head):])
        imgF = StringIO.StringIO()
        imgF.write(imgdata)
        imgF.seek(0)
        img = Image.open(imgF)
        print("Time spent on loading base64 image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        start_time = time.time()
        # flip image horizontally
        buf = cv2.flip(np.asarray(img), flipCode=1)
        # convert BGR to RGB
        rgbFrame = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
        print("Time spent on reversing image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))
        # resize and convert BGR to GRAY for faster face detection
        smallGrayFrame = cv2.resize(buf, (0,0), fx=1.0/resize_ratio, fy=1.0/resize_ratio)
        grayFrame = cv2.cvtColor(smallGrayFrame, cv2.COLOR_BGR2GRAY)
        # grayFrame = cv2.cvtColor(buf, cv2.COLOR_BGR2GRAY)

        ## Dectect Faces ##

        start_time = time.time()
        # Find all the faces and face enqcodings in the frame of Webcam
        face_locations = face_recognition.face_locations(grayFrame)
        print("Time spent on detecting face: {:.2f} ms".format(
            self.processing_time(start_time)
        ))
        start_time = time.time()
        face_encodings = face_recognition.face_encodings(rgbFrame, face_locations)
        print("Time spent on extracting face embeddings: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        start_time = time.time()
        for(top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"

            # Resize to original resolution
            top = top * resize_ratio
            right = right * resize_ratio
            bottom = bottom * resize_ratio
            left = left * resize_ratio

            # Draw a box around the face
            cv2.rectangle(rgbFrame, (left, top), (right, bottom), (153, 255, 204), thickness=2)

            # Draw a labeled name below the face
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(rgbFrame, name, (left, top - 10), font, fontScale=0.75,
                        color=(152, 255, 204), thickness=2)
        print("Time spent on updating image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        start_time = time.time()
        annotatedFrame = np.copy(rgbFrame)
        print("Time spent on copying image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        start_time = time.time()
        # generate image data url from annotated frame
        png_encoded = cv2.imencode('.png', annotatedFrame)
        content = 'data:image/png;base64,' + \
            urllib.quote(base64.b64encode(png_encoded[1]))
        print("Time spent on drawing image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        return(content)

    def processing_time(self, start_time):
        elapsed = (time.time() - start_time) * 1000 # ms
        return(elapsed)


if __name__ == '__main__':
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory("ws://localhost:{}".format(args.port))
    factory.protocol = FaceLearnerProtocol

    reactor.listenTCP(args.port, factory)
    reactor.run()
