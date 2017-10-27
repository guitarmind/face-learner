#!/usr/bin/env python
#
# A simple Web server for static files.
#
# Author: Mark Peng (markpeng.ntu@gmail.com)
#

import tornado.httpserver
import tornado.ioloop
import tornado.web
import argparse
import logging
import os
import time
import pickle

import face_processing as fp
import face_detector as fd
import tts

# Custom Face Object
from face import Face, VizFace


# Face thumbnail
thumbnail_size = 48

# Face model
model_path = None
learned_faces = None

# Recognition tolerance
tolerance = 0.4
# tolerance = 0.45


"""
Logging settings
"""
log_file = "face-learner.access.log"
logger = logging.getLogger('FaceLearner')
logger.setLevel(logging.INFO)
try:
    os.remove(log_file)
except OSError:
    pass
fileHandler = logging.FileHandler(log_file)
fileHandler.setLevel(logging.INFO)
# console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
consoleHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

class CachedDisabledStaticFileHandler(tornado.web.StaticFileHandler):

    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

class DefaultPageHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        with open(os.path.join(os.getcwd(), 'web/index.html')) as f:
            self.write(f.read())
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

class FaceDetectionHandler(tornado.web.RequestHandler):

    def post(self):
        data_url = self.request.body
        frame = fp.data_url_to_rgbframe(data_url)

        # Use custom tolerance if detected
        comparison_tolerance = self.get_argument("tolerance", tolerance)

        # Detect faces inside image
        annotated_data_url, frame_faces = fd.detect_faces(
            frame, thumbnail_size, learned_faces, comparison_tolerance)
        resp = {
            'annotated_snapshot': annotated_data_url,
            'detected_faces': frame_faces
        }
        self.write(resp)

class ModelUpdateHandler(tornado.web.RequestHandler):

    def get(self):
        global model_path, learned_faces
        learned_faces = load_model(model_path)

# Load Pre-trained Face Recongnition Model #

def load_model(model_path):
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        if model is not None:
            print("Loaded model faces:")
            for learned in model:
                print(learned.name, learned.samples)
            print("Model face count: {}".format(len(model)))

    return model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', dest='port', help='the listening port of Web server (default: 8000)')
    parser.add_argument('--model', type=str, default="model/learned_faces.pkl",
                        help='Model file path for learned faces')
    args = parser.parse_args()

    global model_path, learned_faces
    model_path = args.model

    # Load learned model if found
    if os.path.isfile(model_path):
        learned_faces = load_model(model_path)
    else:
        learned_faces = set()

    port = args.port
    if not args.port:   # if port is not given, use the default one 
        port = 8000

    application = tornado.web.Application([
                    (r"/face_detection", FaceDetectionHandler),
                    (r"/model_updated", ModelUpdateHandler),
                    (r"/", DefaultPageHandler),
                    (r'/deps/css/(.*)',CachedDisabledStaticFileHandler,{'path':"web/deps/css"}),
                    (r'/deps/js/(.*)',CachedDisabledStaticFileHandler,{'path':"web/deps/js"}),
                    (r'/deps/fonts/(.*)',CachedDisabledStaticFileHandler,{'path':"web/deps/fonts"}),
                    (r'/js/(.*)',CachedDisabledStaticFileHandler,{'path':"web/js"})])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    logger.info("Web server starts at port " + str(port) + ".")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
