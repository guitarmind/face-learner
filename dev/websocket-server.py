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
# import cv2
# import imagehash
import json
from PIL import Image
import numpy as np
import os
import StringIO
import urllib
import base64
import time

import matplotlib.pyplot as plt

incoming_frame_width = 400
incoming_frame_height = 300

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
            processing_time = (time.time() - start_time) * 1000 # ms
            msg = {
                "type": "ANNOTATED",
                "content": content,
                "processing_time": "{:.2f}".format(processing_time) 
            }
            self.sendMessage(json.dumps(msg))
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def processFrame(self, dataURL, labled):
        head = "data:image/jpeg;base64,"
        assert(dataURL.startswith(head))
        imgdata = base64.b64decode(dataURL[len(head):])
        imgF = StringIO.StringIO()
        imgF.write(imgdata)
        imgF.seek(0)
        img = Image.open(imgF)

        buf = np.fliplr(np.asarray(img))
        # convert RGB to BGR?
        rgbFrame = np.zeros((incoming_frame_height, incoming_frame_width, 3),
                            dtype=np.uint8)
        rgbFrame[:, :, 0] = buf[:, :, 2]
        rgbFrame[:, :, 1] = buf[:, :, 1]
        rgbFrame[:, :, 2] = buf[:, :, 0]

        annotatedFrame = np.copy(buf)

        # generate image data url from annotated frame
        plt.figure()
        plt.imshow(annotatedFrame)
        plt.xticks([])
        plt.yticks([])
        imgdata = StringIO.StringIO()
        plt.savefig(imgdata, format='png', bbox_inches='tight')
        imgdata.seek(0)
        content = 'data:image/png;base64,' + \
            urllib.quote(base64.b64encode(imgdata.buf))
        plt.close()
        
        return(content)

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory("ws://localhost:{}".format(args.port))
    factory.protocol = FaceLearnerProtocol

    reactor.listenTCP(args.port, factory)
    reactor.run()
