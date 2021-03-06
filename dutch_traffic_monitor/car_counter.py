import tempfile
from dutch_traffic_monitor.vehicle_detector_darknet import detect_vehicle_yolov3
import os
from dutch_traffic_monitor.download_traffic_video import download_video_clip
import cv2
from mysql.connector import errorcode
import mysql.connector

AMSTELVEEN_URL = "https://stream.vid.nl:1935/rtplive/IB_207.stream/"
DEFAULT_NS = {"ns": "urn:mpeg:dash:schema:mpd:2011"}


class CarCounterBase:
    """
    Base class for car counter
    """
    # This is the default size from vid.nl
    videos_width_height = (800, 450)

    def __init__(self):
        self.cascade_clf = None
        self.nb_of_cars = []
        self.video_downloaded = ""
        self.video_publish_time = ""
        self.local_dir = ""

    def add_cascade_classifier(self, cls_xml):
        self.cascade_clf = cv2.CascadeClassifier(cls_xml)

    def detect_cars_cascade(self):
        pass

    def detect_cars_nn(self):
        pass

    def download_video(self, url, local_dir):
        self.video_downloaded = download_video_clip(url=url, local_dir=local_dir)
        self.local_dir = local_dir
        self.video_publish_time = self.video_downloaded.split(".")[0]

    def clean_up(self):
        if os.path.exists(self.local_dir):
            os.system("rm -rf {}".format(self.local_dir))
            if not os.path.exists(self.local_dir):
                print("{} is removed".format(self.local_dir))

    @property
    def avg_nb_of_cars(self):
        """
        Get the average number of cars
        :return:
        """
        if self.nb_of_cars:
            return sum(self.nb_of_cars) / len(self.nb_of_cars)


class CarCounterVideo(CarCounterBase):
    def __init__(self):
        super(CarCounterVideo, self).__init__()
        self.video_capture = None
        self._fourcc = None
        self.video_writer = None

    def load_video(self, video_src):
        self.video_capture = cv2.VideoCapture(video_src)
        self._fourcc = cv2.VideoWriter_fourcc('A', 'V', 'C', '1')

    def detect_cars_cascade(self, save_as=None, show_window=True):
        if save_as is not None:
            self.video_writer = cv2.VideoWriter(save_as, self._fourcc, 20.0, CarCounterVideo.videos_width_height)
        while True:
            ret, img = self.video_capture.read()
            if img is None:
                break
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Detect cars
            cars = self.cascade_clf.detectMultiScale(image=gray, scaleFactor=1.1, minNeighbors=1, minSize=(3, 3))
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

    def detect_cars_nn(self, nb_frames=5, save_as=None, show_window=False):
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
            index = index + 1
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
            cars = self.cascade_clf.detectMultiScale(image=gray, scaleFactor=1.1, minNeighbors=1, minSize=(3, 3))
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
        _host = os.getenv("MYSQL_HOST", "localhost")
        _port = os.getenv("MYSQL_PORT", 3306)
        _user = os.getenv("MYSQL_USER_NAME", "root")
        _password = os.getenv("MYSQL_PASSWORD", "mysqladmin")
        self.connection = mysql.connector.connect(user=_user, password=_password,
                                                  host=_host, port=_port, connect_timeout = 10000)
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
            else:
                raise

    def __del__(self):
        if self.connection:
            self.connection.close()

    def insert_record(self, values):
        if not isinstance(values, tuple):
            raise TypeError("expected a tuple, got %s" % type(values))

        self.cursor.execute("insert into traffic.A9 values ('%s', %d)" % values)
        self.connection.commit()
        print("record is inserted:", values)

def video_detector_worker(save_as):
    _local_dir = "local_videos"
    cc = CarCounterVideo()
    cc.download_video(AMSTELVEEN_URL, local_dir=_local_dir)
    cc.load_video(_local_dir + "/" + cc.video_downloaded)
    cc.detect_cars_nn(save_as=save_as, show_window=False, nb_frames=65535)
    print(cc.nb_of_cars)
    print(cc.avg_nb_of_cars)
    cc.clean_up()
    return cc

def main_nn():
    db = MysqlDatabase()
    while True:
        ret = video_detector_worker(save_as=None)
        db.insert_record((ret.video_publish_time, round(ret.avg_nb_of_cars)))



def main_cascade():
    db = MysqlDatabase()
    _local_dir = "local_videos"
    while True:
        cc = CarCounterVideo()
        cc.download_video(AMSTELVEEN_URL, local_dir=_local_dir)
        cc.load_video(_local_dir + "/" + cc.video_downloaded)
        cc.add_cascade_classifier("cars.xml")
        cc.detect_cars_cascade(save_as=None, show_window=False)
        print(cc.avg_nb_of_cars)
        db.insert_record((cc.video_publish_time, round(cc.avg_nb_of_cars)))
        cc.clean_up()


if __name__ == '__main__':
    try:
        main_nn()
    except KeyboardInterrupt:
        print("key board interrupted")
