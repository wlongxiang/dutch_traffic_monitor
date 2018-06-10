import pandas as pd
import tempfile
from darknet import detect_vehicle_yolov3
from download_traffic_video import download_video_clip

from mysql.connector import errorcode
import mysql.connector
AMSTELVEEN_URL = "https://stream.vid.nl:1935/rtplive/IB_207.stream/"
DEFAULT_NS = {"ns": "urn:mpeg:dash:schema:mpd:2011"}
import os

import cv2

class CarCounterBase:
    """
    Base class for car counter
    """
    # This is the defaut size from vid.nl
    videos_width_height = (800, 450)
    def __init__(self):
        self.cascade_clf = None
        self.nb_of_cars = []
        self.video_downloaded = ""
        self.video_publish_time = ""

    def add_cascade_classifier(self, cls_xml):
        self.cascade_clf = cv2.CascadeClassifier(cls_xml)

    def detect_cars_cascade(self):
        pass

    def detect_cars_nn(self):
        pass

    def download_video(self, url, local_dir):
        self.video_downloaded = download_video_clip(url=url, local_dir=local_dir)
        self.video_publish_time = self.video_downloaded.split(".")[0]

    @property
    def avg_nb_of_cars(self):
        """
        Get the average number of cars
        :return:
        """
        if self.nb_of_cars:
            return sum(self.nb_of_cars)/len(self.nb_of_cars)





class CarCounterVideo(CarCounterBase):
    def __init__(self):
        super(CarCounterVideo, self).__init__()
        self.video_capture = None
        self._fourcc = None
        self.video_writer = None

    def load_video(self, video_src):
        self.video_capture = cv2.VideoCapture(video_src)
        self._fourcc = cv2.VideoWriter_fourcc('A', 'V', 'C', '1')


    def detect_cars_cascade(self, save_as=None,show_window=True):
        if save_as is not None:
            self.video_writer = cv2.VideoWriter(save_as, self._fourcc, 20.0, CarCounterVideo.videos_width_height)
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
            if show_window:
                cv2.imshow(self.video_publish_time, img)
            if save_as is not None:
                self.video_writer.write(img)
            # if esc key(27) pressed, break
            if cv2.waitKey(33) == 27:
                break

    def detect_cars_nn(self, nb_frames = 5, save_as = None, show_window = False):
        if save_as is not None:
            self.video_writer = cv2.VideoWriter(save_as, self._fourcc, 20.0, CarCounterVideo.videos_width_height)
        index = 0
        while True:
            ret, img = self.video_capture.read()
            if img is None or index == nb_frames:
                break
            with tempfile.NamedTemporaryFile(suffix=".jpg") as fp:
                cv2.imwrite(fp.name, img)
                # Detect cars
                _nb_of_cars_per_frame, pred_img = detect_vehicle_yolov3(fp.name, show_window=False)

            _cars_trucks = [x[1] for x in _nb_of_cars_per_frame if x[0] in ["car", "truck", "bus"]].__len__()
            self.nb_of_cars.append(_cars_trucks)
            # draw rectangle on detected cars
            # Show the video
            if show_window:
                cv2.imshow(self.video_publish_time, pred_img)
            if save_as is not None:
                self.video_writer.write(pred_img)
            index = index+1
            # if esc key(27) pressed, break
            if cv2.waitKey(33) == 27:
                break
        cv2.destroyAllWindows()

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


class MysqlDatabase:
    DB_NAME = "traffic"
    DDL = "CREATE TABLE traffic.A9( \
    time DATETIME NOT NULL,\
    NbOfCars INT NOT NULL, \
    PRIMARY KEY (time) \
    )"

    def __init__(self):
        self.connection = mysql.connector.connect(user='root', password='mysqladmin',
                                                  host='127.0.0.1', port=3306)
        self.cursor = self.connection.cursor()
        try:
            self.cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(self.DB_NAME))
            print("database {} is created successfully".format(self.DB_NAME))
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DB_CREATE_EXISTS:
                print("database {} already exists".format(self.DB_NAME))
        try:
            self.cursor.execute(self.DDL)
            print("table A9 is created successfully")
        except Exception as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("table A9 already exists")

    def __del__(self):
        if self.connection:
            self.connection.close()

    def insert_record(self, values):
        if not isinstance(values, tuple):
            raise TypeError("expected a tuple, got %s" % type(values))

        self.cursor.execute("insert into traffic.A9 values ('%s', %d)"%values)
        self.connection.commit()


def main_nn():
    db = MysqlDatabase()
    _local_dir = "local_videos"
    cc = CarCounterVideo()
    for x in range(1000):
        cc.download_video(AMSTELVEEN_URL, local_dir=_local_dir)
        cc.load_video(_local_dir +"/"+ cc.video_downloaded)
        cc.detect_cars_nn(save_as="nn_labels_" + cc.video_downloaded, show_window=True)
        print(cc.avg_nb_of_cars)
        db.insert_record((cc.video_publish_time, round(cc.avg_nb_of_cars)))
    ret = db.cursor.execute("select * from traffic.A9")
    r = db.cursor.fetchall()
    print(r)

def main_cascade():
    db = MysqlDatabase()
    _local_dir = "local_videos"
    cc = CarCounterVideo()
    while True:
        cc.download_video(AMSTELVEEN_URL, local_dir=_local_dir)
        cc.load_video(_local_dir +"/"+ cc.video_downloaded)
        cc.add_cascade_classifier("cars.xml")
        cc.detect_cars_cascade(save_as="nn_labels_" + cc.video_downloaded, show_window=True)
        print(cc.avg_nb_of_cars)
        db.insert_record((cc.video_publish_time, round(cc.avg_nb_of_cars)))
    ret = db.cursor.execute("select * from traffic.A9")
    r = db.cursor.fetchall()
    print(r)







if __name__ == '__main__':
    main_cascade()
