#!/usr/bin/env python2

import sys
import cv2

def main(argv):

    # capture from camera at location 0
    cap = cv2.VideoCapture(0)

    # Capture frame-by-frame
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    print(gray.shape)

    width = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    print("Height: ", height)
    print("Width: ", width)

    # When everything done, release the capture
    cap.release()

if __name__ == '__main__':
    main(sys.argv)
