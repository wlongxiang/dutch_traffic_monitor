MPD_FILE_SLOTEN = "https://stream.vid.nl:1935/rtplive/IB_94.stream/manifest.mpd"
AMSTELVEEN_URL = "https://stream.vid.nl:1935/rtplive/IB_207.stream/"
DEFAULT_NS = {"ns": "urn:mpeg:dash:schema:mpd:2011"}
import datetime
import os
import re
import xml.etree.ElementTree as ET
import requests


# Download the manifest file
def _download_manifest(url=AMSTELVEEN_URL, filename="manifest.mpd"):
    r = requests.get(url=url + filename)

    if r.status_code == 200:
        with open("videos/" + filename, "w+") as f:
            f.write(r.text)
    else:
        raise ConnectionError("failed to download manifest file")


# Extract init m4s file from manifest

def _download_mp4(manifest):
    root = ET.parse(manifest).getroot()
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


def download_video_clip(url=AMSTELVEEN_URL):
    # make videos path
    if not os.path.exists("videos"):
        os.mkdir("videos")
    _download_manifest(url=url)
    _download_mp4(manifest="videos/manifest.mpd")


if __name__ == '__main__':
    download_video_clip()
