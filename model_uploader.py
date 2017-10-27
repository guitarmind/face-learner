#!/usr/bin/env python
#
# Model file uploader to remote server
#
# Author: Mark Peng (markpeng.ntu@gmail.com)
#


import json
import time
import requests

import pickle
import os.path
import codecs

# Custom Face Object
from face import Face, VizFace


def load_model(model_path):
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        if model is not None:
            print("Loaded model faces:")
            for learned in model:
                print(learned.name, learned.samples)
            print("Model face count: {}".format(len(model)))

    return model

remote_model_api = "http://localhost:8000/model"
model_path = "model/learned_faces.pkl"
# Load learned model if found
if os.path.isfile(model_path):
    learned_faces = load_model(model_path)
    pickled = codecs.encode(pickle.dumps(learned_faces), "base64").decode()
    body = {
      'cmd': 'overwrite',
      'model': pickled
    }
    r = requests.post(remote_model_api, json=body)
    print(r)
    print("Remote model file updated!")
else:
    print("No model file found!")

