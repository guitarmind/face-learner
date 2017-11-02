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
import json
import numpy as np
import time
import uuid
from threading import Thread
import requests

import pickle
import os.path
import tts

import face_recognition
import face_processing as fp
import face_detector as fd
# Custom Face Object
from face import Face, VizFace


# Face comparison tolerance
# tolerance = 0.45
tolerance = 0.48

# Face thumbnail
thumbnail_size = 48

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=9000,
                    help='WebSocket Port')
parser.add_argument('--model', type=str, default="model/learned_faces.pkl",
                    help='Model file path for learned faces')
args = parser.parse_args()

if not os.path.exists("model"):
    os.makedirs("model")
model_path = args.model


class FaceLearnerProtocol(WebSocketServerProtocol):

    def __init__(self):
        # Call init function of WebSocketServerProtocol
        super(self.__class__, self).__init__()
        self.images = {}
        self.palette = []
        self.palette_hex = []
        # Load learned model if found
        if os.path.isfile(model_path):
            self.load_model()
        else:
            self.learned_faces = set()
        # A cache set of detected faces for drawing
        self.detected_vizfaces = set()
        # A lookup table for drawn faces
        self.face_table = {}
        # A lookup table for face name and uuid
        self.name_table = {}
        # A reference to current training face
        self.training_face = None
        # Used for averaging the embeddings of same training face
        self.training_embeddings = None

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        raw = payload.decode('utf8')
        msg = json.loads(raw)
        # print("Received {} message of length {}.".format(
        #     msg['type'], len(raw)))
        if msg['type'] == "FRAME":
            start_time = time.time()
            content, faces = self.process_frame(msg['dataURL'])
            msg = {
                "type": "ANNOTATED",
                "content": content,
                "frame_faces": faces,
                "processing_time": "{:.2f}".format(self.processing_time(start_time))
            }
            self.sendMessage(json.dumps(msg))
            # Notify front-end to draw new frame
            self.sendMessage('{"type": "PROCESSED"}')
        elif msg['type'] == "LABELED":
            if msg['name'] != "Unknown":
                # Merge unknown face into known one if asked
                if msg['name'] in self.name_table:
                    labeled_face = self.face_table[self.name_table[msg['name']]]
                    face_to_merge = self.face_table[msg['uuid']]
                    labeled_face = self.merge_faces(labeled_face, face_to_merge)
                    del self.face_table[msg['uuid']]
                    self.detected_vizfaces.remove(face_to_merge)
                    self.update_face_to_model(labeled_face)
                    # Play voice
                    self.play_speech("The face of {} has been merged.".format(labeled_face.name))
                else:
                    vizface = self.face_table[msg['uuid']]
                    # Update labeled name of learned face
                    if vizface is not None:
                        vizface.setName(msg['name'])
                        self.update_face_to_model(vizface)
                        if not vizface.name in self.name_table:
                            self.name_table[vizface.name] = vizface.uuid
                        print("Learned faces: {}".format(len(self.learned_faces)))
                        # Play voice
                        self.play_speech("The face of {} has been labeled.".format(vizface.name))

        elif msg['type'] == "PALETTE":
            colors = msg['colors']
            colors_hex = msg['colors_hex']
            self.palette = colors
            self.palette_hex = colors_hex
        elif msg['type'] == "TRAINING":
            start_time = time.time()
            mode = msg['mode']
            vizface = self.face_table[msg['uuid']]
            if vizface is not None:
                if mode == "on":
                    self.training_face = vizface
                    self.training_embeddings = {
                        "summation" : vizface.embeddings,
                        "count" : 0
                    }
                    print("Face trainging starts for {}".format(vizface.name))
                else:
                    current_sum = self.training_embeddings['summation']
                    current_count = self.training_embeddings['count']

                    if current_count > 0:
                        average_embeddings = current_sum / current_count
                        # print("Averaged face embeddings: {}".format(average_embeddings))
                        # print("Original face embeddings: {}".format(self.training_face.embeddings))
                        print("[FACE MODELED] Distance between Averaged and Original face embeddings: {:.3f}".format(
                            fp.L2_distance(average_embeddings, self.training_face.embeddings)))

                        # Update original vizface and learned face
                        vizface.setEmbeddings(average_embeddings)
                        vizface.setSamples(vizface.samples + current_count)
                        self.update_face_to_model(vizface)

                    # Reset all training variables
                    self.training_face = None
                    self.training_embeddings = None
                    print("Face trainging stopped for {}".format(vizface.name))
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def processing_time(self, start_time):
        return (time.time() - start_time) * 1000 # ms

    def process_frame(self, data_url):
        img = fp.data_url_to_rgbframe(data_url)
        img_width, img_height = img.size

        # Flip image horizontally
        flipped_frame = fp.flip_image(img)
        # Convert BGR to RGB
        rgb_frame = fp.gbrframe_to_rgbframe(flipped_frame)

        # Make a copy for annotation
        annotated_frame = np.copy(rgb_frame)

        # Convert BGR to GRAY for faster face detection
        grayFrame = fp.gbrframe_to_grayframe(rgb_frame)

        ## Dectect Faces ##

        start_time = time.time()
        # Find all the faces and face enqcodings in the frame of Webcam
        face_locations = face_recognition.face_locations(rgb_frame)
        print("Time spent on detecting face: {:.2f} ms".format(
            self.processing_time(start_time)
        ))
        start_time = time.time()
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        print("Time spent on extracting face embeddings: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        frame_faces = []
        print("[NEW FRAME] Detected faces: {}".format(len(face_encodings)))
        for(top, right, bottom, left), embeddings in zip(face_locations, face_encodings):
            start_time = time.time()
            result_face, distance = self.face_lookup(embeddings)
            print("Time spent on face lookup: {:.2f} ms".format(
                self.processing_time(start_time)
            ))
            sample_counter = 0
            if self.training_face != None and result_face == self.training_face and len(face_locations) == 1:
                current_sum = self.training_embeddings['summation']
                current_count = self.training_embeddings['count']
                self.training_embeddings['summation'] = np.add(current_sum, embeddings)
                self.training_embeddings['count'] = current_count + 1
                sample_counter = self.training_embeddings['count']

            color = result_face.color
            cropped = fp.crop_rgbframe(rgb_frame, top, right, bottom, left, (img_width, img_height))
            if cropped.size > 0:
                resized = fp.resize_rgbframe(cropped, thumbnail_size, thumbnail_size)
                data_url = fp.rgbframe_to_data_url(resized)
                face = {
                    "uuid": result_face.uuid,
                    "color": result_face.color_hex,
                    "name": result_face.name,
                    "thumbnail": data_url,
                    "samples": result_face.samples + sample_counter
                }
            else:
                face = {
                    "uuid": result_face.uuid,
                    "color": result_face.color_hex,
                    "name": result_face.name,
                    "samples": result_face.samples + sample_counter
                }
            frame_faces.append(face)

            # Draw a box around the face (color order: BGR)
            fp.draw_face_box(annotated_frame, color, top, right, bottom, left)

            # Draw a labeled name below the face (color order: BGR)
            fp.draw_face_label_text(annotated_frame, result_face.name, color, left, top - 10)

            # Draw matched distance
            fp.draw_face_label_text(annotated_frame, "{:.3f}".format(distance), color,
                left + int((right - left) / 2) - 20, bottom + 20, 0.5, 1)

        start_time = time.time()
        # Generate image data url from annotated frame
        content = fp.rgbframe_to_data_url(annotated_frame)
        print("Time spent on converting image to data url: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

        return content, frame_faces 

    def face_lookup(self, unknown):

        # Lookup from detected faces first
        matched_vizfaces = []
        for known in self.detected_vizfaces:
            matched, distance = self.compare_faces(known.embeddings, unknown, tolerance)
            if matched:
                matched_vizfaces.append((known, distance))
        if len(matched_vizfaces) > 0:
            known, min_dist = sorted(matched_vizfaces, key=lambda x: x[1])[0]
            return known, min_dist

        matched_learned_faces = []
        for known in self.learned_faces:
            matched, distance = self.compare_faces(known.embeddings, unknown, tolerance)
            if matched:
                color_index = len(self.detected_vizfaces) if len(self.detected_vizfaces) > 0 else 0
                color, color_hex = fd.pick_face_color(color_index)
                vizface = VizFace(known.uuid, known.name, known.embeddings, known.samples,
                            color, color_hex)
                self.detected_vizfaces.add(vizface)
                self.face_table[known.uuid] = vizface
                matched_learned_faces.append((vizface, distance))
        if len(matched_learned_faces) > 0:
            known, min_dist = sorted(matched_learned_faces, key=lambda x: x[1])[0]
            return known, min_dist

        # Not found, create a new one
        uid = str(uuid.uuid4())
        name = "Unknown"
        color_index = len(self.detected_vizfaces) if len(self.detected_vizfaces) > 0 else 0
        color, color_hex = fd.pick_face_color(color_index)
        vizface = VizFace(uid, name, unknown, 0, color, color_hex)
        self.detected_vizfaces.add(vizface)
        self.face_table[uid] = vizface

        return vizface, 999

    def load_model(self):
        with open(model_path, "rb") as f:
            model = pickle.load(f)
            if model is not None:
                print("Loaded model faces:")
                for learned in model:
                    print(learned.name, learned.samples)
                print("Model face count: {}".format(len(model)))
                self.learned_faces = model

    def save_model(self):
        with open(model_path, "wb") as f:
            pickle.dump(self.learned_faces, f,
                protocol=pickle.HIGHEST_PROTOCOL)
        self.send_model_updated_event()

    def send_model_updated_event(self):
        requests.get("http://localhost:8000/model_updated")

    def update_face_to_model(self, vizface):
        learned = Face(vizface.uuid, vizface.name, vizface.embeddings, vizface.samples)
        if vizface in self.detected_vizfaces:
            self.detected_vizfaces.remove(vizface)
        self.detected_vizfaces.add(vizface)
        if learned in self.learned_faces:
            self.learned_faces.remove(learned)
        self.learned_faces.add(learned)
        # Update model file
        self.save_model()

    def compare_faces(self, known, unknown, tolerance=0.6):
        distance = fp.L2_distance(known, unknown)
        return distance <= tolerance, distance

    def merge_faces(self, original, new):
        if original.samples > 0 and new.samples >= 0:
            new_count = 1
            if new.samples > 0:
                new_count = new.samples
            total_counts = float(original.samples + new_count)
            updated_embeddings = (original.samples / total_counts) * original.embeddings + \
                (new_count / total_counts) * new.embeddings
            original.setEmbeddings = updated_embeddings
            original.setSamples = total_counts
        return original

    def play_speech(self, text):
        thread = Thread(target=self.text_to_speech, args=(text,))
        thread.daemon = True # Daemonize thread
        thread.start()       # Start the execution

    def text_to_speech(self, text):
        start_time = time.time()
        tts.text_to_speech(text)
        print("Time spent on text to speech: {:.2f} ms".format(
            self.processing_time(start_time)
        ))

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory("ws://localhost:{}".format(args.port))
    factory.protocol = FaceLearnerProtocol

    reactor.listenTCP(args.port, factory)
    reactor.run()
