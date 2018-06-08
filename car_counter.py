import datetime
import re
import xml.etree.ElementTree as ET
import requests

from darknet import detect_vehicle_yolov3
from download_traffic_video import download_video_clip

AMSTELVEEN_URL = "https://stream.vid.nl:1935/rtplive/IB_207.stream/"
DEFAULT_NS = {"ns": "urn:mpeg:dash:schema:mpd:2011"}
import os

import cv2

class CarCounterBase:
    # This is the defaut size from vid.nl
    videos_width_height = (800, 450)
    def __init__(self):
        self.cascade_clf = None
        self.nb_of_cars = []
        self.video_downloaded = ""

    def add_cascade_classifier(self, cls_xml):
        self.cascade_clf = cv2.CascadeClassifier(cls_xml)

    def detect_cars_cascade(self):
        pass

    def detect_cars_nn(self):
        pass

    def dowlod_video(self, url, local_dir):
        self.video_downloaded = download_video_clip(url=url, local_dir=local_dir)


class CarCounterVideo(CarCounterBase):
    def __init__(self):
        super(CarCounterVideo, self).__init__()
        self.video_capture = None
        self._fourcc = None
        self.video_writer = None

    def load_video(self, video_src):
        self.video_capture = cv2.VideoCapture(video_src)
        self._fourcc = cv2.VideoWriter_fourcc('A', 'V', 'C', '1')


    def detect_cars_cascade(self):
        while True:
            ret, img = self.video_capture.read()
            if img is None:
                break
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Detect cars
            cars = self.cascade_clf.detectMultiScale(image=gray, scaleFactor=1.1, minNeighbors=1, minSize=(3,3))
            self.nb_of_cars.append(len(cars))
            # draw rectangle on detected cars
            for (x, y, w, h) in cars:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            # Show the video
            cv2.imshow('video', img)
            self.video_writer.write(img)
            # if esc key(27) pressed, break
            if cv2.waitKey(33) == 27:
                break

    def detect_cars_nn(self, save_as = "predictions.mp4"):
        self.video_writer = cv2.VideoWriter(save_as, self._fourcc, 20.0, CarCounterVideo.videos_width_height)
        index = 0
        while True:
            ret, img = self.video_capture.read()
            filename = "{}-{}.jpg".format("darknet", index)
            if not os.path.exists("temp_images"):
                os.mkdir("temp_images")
            cv2.imwrite("temp_images/"+filename, img)
            if img is None:
                break
            # Detect cars
            self.nb_of_cars, pred_img = detect_vehicle_yolov3(os.getcwd()+"/temp_images/"+filename, show_window=False)
            # draw rectangle on detected cars
            cv2.imwrite("temp_images/" + "labeled_"+ filename, pred_img)
            # Show the video
            cv2.imshow('video', pred_img)
            self.video_writer.write(pred_img)
            index = index+1
            # if esc key(27) pressed, break
            if cv2.waitKey(33) == 27:
                break

class CarCounterimage(CarCounterBase):
    def __init__(self):
        super(CarCounterimage, self).__init__()
        self.image = None
        self.image_path = ""

    def load_image(self, image_src):
        self.image = cv2.imread(image_src)
        self.image_path = image_src

    def detect_cars_cascade(self):
        while True:
            # Convert to grayscale
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            # Detect cars
            cars = self.cascade_clf.detectMultiScale(image=gray, scaleFactor=1.1, minNeighbors=1, minSize=(3,3))
            self.nb_of_cars.append(len(cars))
            # draw rectangle on detected cars
            for (x, y, w, h) in cars:
                cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            # Show the video
            cv2.imshow('image', self.image)
            # Show the result for 3 seconds
            if cv2.waitKey() == 27:
                break
        cv2.destroyAllWindows()

    def detect_cars_nn(self, threshold=0.5):
        self.nb_of_cars, pred_img = detect_vehicle_yolov3(self.image_path, threshold=threshold)




if __name__ == '__main__':
    cascade_src = 'cars.xml'

    cc = CarCounterVideo()
    cc.dowlod_video(AMSTELVEEN_URL, local_dir="my_v")
    cc.load_video("my_v/"+ cc.video_downloaded)
    cc.detect_cars_nn(save_as="predictions.mp4")
