import subprocess
import cv2
import os
import requests

__cur_dir__ = os.path.dirname(__file__)
def detect_vehicle_yolov3(img_src, threshold=0.25):
    # 0.2 is a empirical guess based on random test on aveen a9 video frames
    # Check here for setting threshold: https://pjreddie.com/darknet/yolo/
    # Download the weights if not there
    if not os.path.isfile("weights/yolov3.weights"):
        r = requests.get("https://pjreddie.com/media/files/yolov3.weights")
        with open("weights/yolov3.weights", "wb") as f:
            f.write(r.content)

    cmd = "./darknet detect cfg/yolov3.cfg weights/yolov3.weights %s -thresh %s" % (img_src, threshold)
    ret = subprocess.check_output(cmd, shell=True, cwd=__cur_dir__)
    ret = ret.decode().splitlines()
    # remove the first element in th return which is like "2-darknet.png: Predicted in 9.295985 seconds."
    _list = []
    for x in ret[1:]:
        label, confidence = x.split(": ")
        _list.append((label, float(confidence.strip('%')) / 100.0))
    pred_img = cv2.imread(__cur_dir__ +"/predictions_day.png")
    return _list, pred_img


if __name__ == '__main__':
    ret, img = detect_vehicle_yolov3("../static/bike_on_way.jpeg")
    print(ret)
    # pass
