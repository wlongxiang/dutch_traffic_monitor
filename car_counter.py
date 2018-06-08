import datetime
import re
import xml.etree.ElementTree as ET
import requests

from darknet import detect_vehicle_yolov3

MPD_FILE_SLOTEN = "https://stream.vid.nl:1935/rtplive/IB_94.stream/manifest.mpd"
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

    @staticmethod
    def _download_manifest(url=AMSTELVEEN_URL, filename="manifest.mpd"):
        r = requests.get(url + filename)
        if r.status_code == 200:
            with open("videos/" + filename, "w+") as f:
                f.write(r.text)
        else:
            raise ConnectionError("failed to download manifest file")

    # Extract init m4s file from manifest

    @staticmethod
    def _download_mp4(manifest_file):
        root = ET.parse(manifest_file).getroot()
        timestamp = root.find("ns:Period/ns:AdaptationSet/ns:SegmentTemplate/ns:SegmentTimeline/ns:S",
                              namespaces=DEFAULT_NS).attrib["t"]
        representation_id = root.find("ns:Period/ns:AdaptationSet/ns:Representation",
                                      namespaces=DEFAULT_NS).attrib["id"]
        media = root.find("ns:Period/ns:AdaptationSet/ns:SegmentTemplate",
                          namespaces=DEFAULT_NS).attrib["media"]
        init_file_template = root.find("ns:Period/ns:AdaptationSet/ns:SegmentTemplate",
                                       namespaces=DEFAULT_NS).attrib["initialization"]

        init_file = re.sub(pattern="\$RepresentationID\$", repl=representation_id, string=init_file_template)
        print("Dowloading init file", init_file)
        _segment = re.sub(pattern="\$Time\$", repl=timestamp, string=media)
        segment = re.sub(pattern="\$RepresentationID\$", repl=representation_id, string=_segment)
        print("Dowloading first segment", segment)
        init_m4s = requests.get(AMSTELVEEN_URL + init_file)
        with open("videos/init.m4s", "wb+") as f:
            f.write(init_m4s.content)

        segment_m4s = requests.get(AMSTELVEEN_URL + segment)
        with open("videos/segment.m4s", "wb+") as f:
            f.write(segment_m4s.content)
        time_now = datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%s")
        print("Concatenating mp4", "traffic%s.mp4" % time_now)
        r = os.system("cat videos/init.m4s videos/segment.m4s > videos/traffic%s.mp4" % time_now)
        if r != 0:
            raise OSError("failed to concat init file and segment file")
        return "traffic%s.mp4" % time_now

    def download_video_clip(self, url=AMSTELVEEN_URL):
        # make videos path
        if not os.path.exists("videos"):
            os.mkdir("videos")
        self._download_manifest(url=url)
        self.video_downloaded = self._download_mp4(manifest_file="videos/manifest.mpd")

    @property
    def count_mean(self):
        return round(sum(self.nb_of_cars)/len(self.nb_of_cars))


class CarCounterVideo(CarCounterBase):
    def __init__(self):
        super(CarCounterVideo, self).__init__()
        self.video_capture = None
        self._fourcc = None
        self.video_writer = None

    def load_video(self, video_src):
        self.video_capture = cv2.VideoCapture(video_src)
        self._fourcc = cv2.VideoWriter_fourcc('A', 'V', 'C', '1', )
        self.video_writer = cv2.VideoWriter("mod_video.mp4", self._fourcc, 20.0, CarCounterVideo.videos_width_height)

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

    def detect_cars_nn(self):
        index = 0
        while True:
            ret, img = self.video_capture.read()
            filename = "{}-{}.jpg".format("darknet", index)
            if not os.path.exists("static"):
                os.mkdir("static")
            cv2.imwrite("static/"+filename, img)
            if img is None:
                break
            # Detect cars
            self.nb_of_cars, pred_img = detect_vehicle_yolov3(os.getcwd()+"/static/"+filename)
            # draw rectangle on detected cars
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
            if cv2.waitKey(3000):
                break
        cv2.destroyAllWindows()

    def detect_cars_nn(self):
        while True:
            # Detect cars
            self.nb_of_cars, pred_img = detect_vehicle_yolov3(self.image_path)
            # draw rectangle on detected cars

            # Show the video
            cv2.imshow('image', self.image)
            # Show the result for 3 seconds
            if cv2.waitKey(3000):
                break
        cv2.destroyAllWindows()




if __name__ == '__main__':
    cascade_src = 'cars.xml'

    # cc = CarCounterVideo()
    # cc.download_video_clip()
    # cc.load_video("./videos/"+cc.video_downloaded)
    # cc.add_cascade_classifier(cascade_src)
    # cc.detect_cars_cascade()
    # # # cc.detect_cars_nn()
    # print("average number of cars in all frames", cc.nb_of_cars)
    # print("average number of cars in all frames", cc.count_mean)

    cc_img = CarCounterimage()
    # cc_img.download_video_clip()
    cc_img.load_image(image_src="/Users/benjamin.wang/devel/data_science/dutch_traffic_monitor/static/night.png")
    # cc_img.add_cascade_classifier(cascade_src)
    cc_img.detect_cars_nn()
    print(cc_img.nb_of_cars)

