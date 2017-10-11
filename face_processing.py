#!/usr/bin/env python2
#
# Face processing and image drawing functions.
#

from PIL import Image
import base64
import cv2
import numpy as np
import os
import StringIO
import urllib

def data_url_to_rgbframe(data_url):
    head = "data:image/jpeg;base64,"
    assert(data_url.startswith(head))
    imgdata = base64.b64decode(data_url[len(head):])
    imgF = StringIO.StringIO()
    imgF.write(imgdata)
    imgF.seek(0)
    img = Image.open(imgF)
    return img

def rgbframe_to_data_url(frame, img_type="jpg"):
    if img_type == "jpg":
        encoded = cv2.imencode('.jpg', frame)
        data_url = 'data:image/jpg;base64,' + \
            urllib.quote(base64.b64encode(encoded[1]))
    else:
        encoded = cv2.imencode('.png', frame)
        data_url = 'data:image/png;base64,' + \
            urllib.quote(base64.b64encode(encoded[1]))
    return data_url

def flip_image(img):
    return cv2.flip(np.asarray(img), flipCode=1)

def gbrframe_to_rgbframe(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def gbrframe_to_grayframe(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

def _trim_to_bounds(rect, image_shape):
    # Make sure a tuple in (top, right, bottom, left) order is within the bounds of the image
    return max(rect[0], 0), min(rect[1], image_shape[1]), min(rect[2], image_shape[0]), max(rect[3], 0)

def crop_rgbframe(frame, top, right, bottom, left, image_shape):
    top, right, bottom, left = _trim_to_bounds((top, right, bottom, left), image_shape)
    width = right - left
    height = bottom - top
    cropped = frame[top:(top + height), left:(left + width)]
    return cropped

def resize_rgbframe(frame, width, height):
    return cv2.resize(frame, (width, height))

def draw_face_box(frame, color, top, right, bottom, left):
    if isinstance(color, tuple):
        cv2.rectangle(frame, (left, top), (right, bottom),
            color, thickness=2)
    else:
        cv2.rectangle(frame, (left, top), (right, bottom),
            (color['b'], color['g'], color['r']), thickness=2)

def draw_face_label_text(frame, text, color, x, y, fontScale=0.75, thickness=2):
    font = cv2.FONT_HERSHEY_DUPLEX
    if isinstance(color, tuple):
        cv2.putText(frame, text, (x, y), font, fontScale=fontScale,
            color=color, thickness=thickness)
    else:
        cv2.putText(frame, text, (x, y), font, fontScale=fontScale,
            color=(color['b'], color['g'], color['r']), thickness=thickness)

def frame_to_image_file(frame, folder_path, filename):
    cv2.imwrite(os.path.join(folder_path , filename), frame)

# Compute Euclidean distance
def L2_distance(face, face_to_compare):
    return np.linalg.norm(face - face_to_compare)
