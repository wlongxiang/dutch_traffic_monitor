import cv2
import os

def extract_frames_from_video(video_src, file_name, dir):
    cap = cv2.VideoCapture(video_src)
    if not os.path.exists(dir):
        os.mkdir(dir)
    index = 0
    while True:
        res, img_array = cap.read()
        if img_array is None:
            break
        cv2.imwrite("{}/{}-{}".format(dir, index, file_name), img_array)
        print("extract {}-{} to directory {}".format(index, file_name, dir))
        index = index + 1

if __name__ == '__main__':
    extract_frames_from_video("sample_videos/traffic_afternoon_18-06-06-15-41-1528292480.mp4", "afternoon.png", "me")