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
import uuid

import pickle
import os.path
import face_recognition

incoming_frame_width = 400
incoming_frame_height = 300
# Disable resize as it causes small faces hard to detect
resize_ratio = 1
if not os.path.exists("model"):
    os.makedirs("model")
model_path = "model/learned_faces.pkl"

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=9000,
                    help='WebSocket Port')
args = parser.parse_args()

# Unique face object
class Face:
    def __init__(self, uuid, name, embeddings):
        self.uuid = uuid
        self.name = name
        self.embeddings = embeddings

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)

    def __repr__(self):
        return "{{uuid: {}, name: {}, embeddings[0:5]: {}}}".format(
            self.uuid,
            self.name,
            self.embeddings[0:5]
        )

class FaceLearnerProtocol(WebSocketServerProtocol):

    def __init__(self):
        # Call init function of WebSocketServerProtocol
        super(self.__class__, self).__init__()
        self.images = {}
        self.palette = []
        self.palette_hex = []
        # Load learned model if found
        global model_path
        if os.path.isfile(model_path):
            with open(model_path, "rb") as f:
                model = pickle.load(f)
                if model is not None:
                    self.learned_faces = model
        else:
            self.learned_faces = set()
        # A cache set of detect faces
        self.detected_faces = set()

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
            content, faces = self.processFrame(msg['dataURL'])
            msg = {
                "type": "ANNOTATED",
                "content": content,
                "frame_faces": faces,
                "processing_time": "{:.2f}".format(self.processing_time(start_time))
            }
            self.sendMessage(json.dumps(msg))
        elif msg['type'] == "LABELED":
            # update labeled name of learned face
            face_obj = None
            for known in self.detected_faces:
                if known.uuid == msg['uuid']:
                    face_obj = known
                    break
            print(face_obj)
            if face_obj is not None:
                face_obj.name = msg['name']
                self.detected_faces.add(face_obj)
        elif msg['type'] == "PALETTE":
            start_time = time.time()
            colors = msg['colors']
            colors_hex = msg['colors_hex']
            self.palette = colors
            self.palette_hex = colors_hex
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def processFrame(self, dataURL):
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
        # Flip image horizontally
        buf = cv2.flip(np.asarray(img), flipCode=1)
        # Convert BGR to RGB
        rgbFrame = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
        print("Time spent on reversing image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))
        # Resize and convert BGR to GRAY for faster face detection
        smallGrayFrame = cv2.resize(buf, (0,0), fx=1.0/resize_ratio, fy=1.0/resize_ratio)
        grayFrame = cv2.cvtColor(smallGrayFrame, cv2.COLOR_BGR2GRAY)

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
        frame_faces = []
        print("Detected faces: {}".format(len(face_encodings)))
        for(top, right, bottom, left), embeddings in zip(face_locations, face_encodings):
            name = "Unknown"

            # Check if the face has been learned before
            result = self.face_lookup(embeddings)
            if result is None:
                uid = str(uuid.uuid4())
                face_obj = Face(uid, name, face_encodings)
                self.learned_faces.add(face_obj)

                # Update learned faces to model file
                with open(model_path, "wb") as f:
                    pickle.dump(self.learned_faces, f,
                        protocol=pickle.HIGHEST_PROTOCOL)
                print('New face learned!')
            else:
                uid = result.uuid
                name = result.name
                face_obj = Face(uid, name, face_encodings)

            color_index = len(self.detected_faces) - 1 if len(self.detected_faces) > 0 else 0
            color = self.palette[color_index % 10]
            color_hex = self.palette_hex[color_index % 10]
            face = {
                "uuid": uid,
                "color": color_hex,
                "name": name
            }
            frame_faces.append(face)
            self.detected_faces.add(face_obj)

            # Resize to original resolution
            top = top * resize_ratio
            right = right * resize_ratio
            bottom = bottom * resize_ratio
            left = left * resize_ratio

            # Draw a box around the face (color order: BGR)
            cv2.rectangle(rgbFrame, (left, top), (right, bottom),
                (color['b'], color['g'], color['r']), thickness=2)

            # Draw a labeled name below the face (color order: BGR)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(rgbFrame, name, (left, top - 10), font, fontScale=0.75,
                color=(color['b'], color['g'], color['r']), thickness=2)

        print("Time spent on updating image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        start_time = time.time()
        annotatedFrame = np.copy(rgbFrame)
        print("Time spent on copying image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        start_time = time.time()
        # Generate image data url from annotated frame
        png_encoded = cv2.imencode('.png', annotatedFrame)
        content = 'data:image/png;base64,' + \
            urllib.quote(base64.b64encode(png_encoded[1]))
        print("Time spent on drawing image: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        return content, frame_faces

    def processing_time(self, start_time):
        elapsed = (time.time() - start_time) * 1000 # ms
        return(elapsed)

    def face_lookup(self, unknown):
        if len(self.learned_faces) > 0:
            # Lookup from detected faces first
            for known in self.detected_faces:
                matched = face_recognition.compare_faces(known.embeddings, unknown, tolerance=0.6)
                if matched:
                    return known
            for known in self.learned_faces:
                matched = face_recognition.compare_faces(known.embeddings, unknown, tolerance=0.6)
                if matched:
                    return known
        else:
            return None

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory("ws://localhost:{}".format(args.port))
    factory.protocol = FaceLearnerProtocol

    reactor.listenTCP(args.port, factory)
    reactor.run()
