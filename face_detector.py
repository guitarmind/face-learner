#!/usr/bin/env python2
#
# Face detection and recognition functions.
#

import face_recognition
import face_processing as fp
import numpy as np
import time
import uuid

# Custom Face Object
from face import Face, VizFace

palette_hex_table = [
  "#a6cee3",
  "#1f78b4",
  "#b2df8a",
  "#33a02c",
  "#fb9a99",
  "#e31a1c",
  "#fdbf6f",
  "#ff7f00",
  "#cab2d6",
  "#6a3d9a"
]
# Convert to BGR colors
palette_bgr_table = [tuple(int(h.lstrip('#')[i:i+2], 16) for i in (4, 2 ,0)) \
    for h in palette_hex_table]

# Pick a color for a new face
def pick_face_color(color_index):
    color_hex = palette_hex_table[color_index % 10]
    color = palette_bgr_table[color_index % 10]
    return color, color_hex

def processing_time(start_time):
    return (time.time() - start_time) * 1000 # ms

def detect_faces(frame, thumbnail_size, learned_faces, tolerance):
    img_width, img_height = frame.shape[1], frame.shape[0]

    # Flip image horizontally
    flipped_frame = fp.flip_image(frame)

    # Already in RGB
    rgb_frame = flipped_frame

    # Make a copy for annotation
    annotated_frame = np.copy(rgb_frame)

    ## Dectect Faces ##

    start_time = time.time()
    # Find all the faces and face enqcodings in the frame of Webcam
    face_locations = face_recognition.face_locations(rgb_frame)
    print("Time spent on detecting face: {:.2f} ms".format(
        processing_time(start_time)
    ))
    start_time = time.time()
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    print("Time spent on extracting face embeddings: {:.2f} ms".format(
        processing_time(start_time)
    ))

    frame_faces = []
    print("[NEW FRAME] Detected faces: {}".format(len(face_encodings)))
    for(top, right, bottom, left), embeddings in zip(face_locations, face_encodings):
        start_time = time.time()
        result_face, distance = face_lookup(embeddings, learned_faces, tolerance)
        print("Time spent on face lookup: {:.2f} ms".format(
            processing_time(start_time)
        ))

        color = result_face.color
        cropped = fp.crop_rgbframe(rgb_frame, top, right, bottom, left,
            (img_width, img_height))
        if cropped.size > 0:
            resized = fp.resize_rgbframe(cropped, thumbnail_size, thumbnail_size)
            data_url = fp.rgbframe_to_data_url(resized)
            face = {
                "uuid": result_face.uuid,
                "color": result_face.color_hex,
                "name": result_face.name,
                "thumbnail": data_url
            }
        else:
            face = {
                "uuid": result_face.uuid,
                "color": result_face.color_hex,
                "name": result_face.name
            }
        frame_faces.append(face)

        # Draw a box around the face (color order: BGR)
        fp.draw_face_box(annotated_frame, color, top, right, bottom, left)

        # Draw a labeled name below the face (color order: BGR)
        fp.draw_face_label_text(annotated_frame, result_face.name,
            color, left - 5, top - 10, 0.65, 2)

        # Draw matched distance
        fp.draw_face_label_text(annotated_frame,
            "{:.3f}".format(distance), color,
            left + int((right - left) / 2) - 20, bottom + 20, 0.5, 1)

    start_time = time.time()
    # Generate image data url from annotated frame
    annotated_data_url = fp.rgbframe_to_data_url(annotated_frame)
    print("Time spent on converting image to data url: {:.2f} ms".format(
        processing_time(start_time)
    ))

    return annotated_data_url, frame_faces

def face_lookup(unknown, learned_faces, tolerance):
    matched_learned_faces = []
    color_index = 0
    for known in learned_faces:
        matched, distance = compare_faces(known.embeddings, unknown, tolerance)
        if matched:
            color, color_hex = pick_face_color(color_index)
            vizface = VizFace(known.uuid, known.name, known.embeddings, known.samples,
                        color, color_hex)
            matched_learned_faces.append((vizface, distance))
        color_index += 1
    if len(matched_learned_faces) > 0:
        known, min_dist = sorted(matched_learned_faces, key=lambda x: x[1])[0]
        return known, min_dist

    # Not found, create a new one
    uid = str(uuid.uuid4())
    name = "Unknown"
    color_index = 0
    color, color_hex = pick_face_color(color_index)
    vizface = VizFace(uid, name, unknown, 0, color, color_hex)
    return vizface, 999

def compare_faces(known, unknown, tolerance=0.6):
    distance = fp.L2_distance(known, unknown)
    return distance <= tolerance, distance

