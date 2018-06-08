import cv2
import os

def extract_frames_from_video(video_src, file_name):
    cap = cv2.VideoCapture(video_src)
    if not os.path.exists("static"):
        os.mkdir("static")
    index = 0
    while True:
        res, img_array = cap.read()
        if img_array is None:
            break
        cv2.imwrite("static/{}-{}".format(file_name, index), img_array)
        index = index + 1

if __name__ == '__main__':
    extract_frames_from_video("videos/traffic18-06-03-20-26-1528050400.mp4", "darknet.png")