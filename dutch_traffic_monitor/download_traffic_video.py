import datetime
import os
import re
import xml.etree.ElementTree as ET
import requests

AMSTELVEEN_URL = "https://stream.vid.nl:1935/rtplive/IB_207.stream/"
DEFAULT_NS = {"ns": "urn:mpeg:dash:schema:mpd:2011"}


# Extract init m4s file from manifest

def _download_mp4(manifest, local_dir):
    root = ET.parse(manifest).getroot()
    _publish_time = root.attrib["publishTime"]
    time_amsterdam = datetime.datetime.strptime(_publish_time, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=2)
    segment_timeline = root.find("ns:Period/ns:AdaptationSet/ns:SegmentTemplate/ns:SegmentTimeline/ns:S",
                                 namespaces=DEFAULT_NS).attrib["t"]
    representation_id = root.find("ns:Period/ns:AdaptationSet/ns:Representation",
                                  namespaces=DEFAULT_NS).attrib["id"]
    media = root.find("ns:Period/ns:AdaptationSet/ns:SegmentTemplate",
                      namespaces=DEFAULT_NS).attrib["media"]
    init_file_template = root.find("ns:Period/ns:AdaptationSet/ns:SegmentTemplate",
                                   namespaces=DEFAULT_NS).attrib["initialization"]

    init_file = re.sub(pattern="\$RepresentationID\$", repl=representation_id, string=init_file_template)
    _segment = re.sub(pattern="\$Time\$", repl=segment_timeline, string=media)
    segment = re.sub(pattern="\$RepresentationID\$", repl=representation_id, string=_segment)
    init_m4s = requests.get(AMSTELVEEN_URL + init_file)
    if init_m4s.status_code == 200:
        _init_file_path = os.path.join(local_dir, "init.m4s")
        print("Dowloading init file", init_file)
        with open(_init_file_path, "wb+") as f:
            f.write(init_m4s.content)

    segment_m4s = requests.get(AMSTELVEEN_URL + segment)
    if segment_m4s.status_code == 200:
        _segment_file_path = os.path.join(local_dir, "segment.m4s")
        print("Dowloading first segment", segment)
        with open(_segment_file_path, "wb+") as f:
            f.write(segment_m4s.content)

    print("Concatenating mp4", time_amsterdam)
    _mp4_file_name = "{}.mp4".format(time_amsterdam.strftime("%Y-%m-%d-%H-%M-%S"))
    _mp4_file_path = os.path.join(local_dir, _mp4_file_name)
    r = os.system("cat {} {} > {}".format(_init_file_path, _segment_file_path, _mp4_file_path))
    if r != 0:
        raise OSError("failed to concat init file and segment file")

    return _mp4_file_name


def download_video_clip(url, local_dir):
    # make local path
    if not os.path.exists(local_dir):
        os.mkdir(local_dir)
    _manifest_path = os.path.join(local_dir, "manifest.mpd")
    r = requests.get(url=url + "manifest.mpd", timeout=10)
    if r.status_code == 200:
        with open(_manifest_path, "w+") as f:
            f.write(r.text)
    else:
        raise ConnectionError("failed to download manifest file")
    return _download_mp4(manifest=_manifest_path, local_dir=local_dir)


if __name__ == '__main__':
    download_video_clip(AMSTELVEEN_URL, "downloaded_videos")
