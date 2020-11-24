#!./venv/bin/python

"""
Project for playing with audio files.
Merge audio files together, over lay them, etc.
"""
import configparser
import json
import logging
import os
import sys
import random

from time import sleep
from pathlib import Path
from pydub import AudioSegment
from multiprocessing import Pool

#Define config and logger.
CONFIG = configparser.ConfigParser()
CONFIG.read("conf/config.ini")
SECTION = "audiomux"

# Use half the availablle threads.
THREADS = int(len(os.sched_getaffinity(0))/2)

# TODO: Get file ready for git, use pod and editted folders for processing.

logger = logging.getLogger(SECTION)

pod_path = Path(Path.cwd()) / "data" / "napoleon" / "pod"
edit_path = Path(Path.cwd()) / "data" / "napoleon" / "editted"

def pool_extract():
    """
    Multi proc function to quickly process multiple tracks.
    """
    
    files = sorted(os.listdir(pod_path))

    with Pool(THREADS) as proc:
        print(proc.map(clip_audio, files))

def clip_audio(pod):
    """
    Used for clipping pod.
    
    Simple function that allows you to edit out 
    first and last few seconds of the pod, for removing ads/etc.

    Args:
        pod (Path): Path to track.
    """

    start = 30
    bookend = 15

    logger.info(f"Converting: {pod}")

    logger.debug("Loading...")
    song = AudioSegment.from_file(pod_path / pod)
    logger.debug("Cutting...")
    song = song[start:bookend*1000]

    try:
        # Create dir for editted outputs, if it doesnt exist.
        edit_path.mkdir()
    except Exception as exp:
        logger.debug(exp)

    out = edit_path / pod
    logger.debug("Extracting...")
    song.export(out, format="mp3")
    logger.info(f"Finished: {pod}")

    # for pod in files:
    #     logger.info(f"Converting: {pod}")

    #     logger.info("Loading...")
    #     song = AudioSegment.from_file(pod_path / pod)
    #     logger.info("Cutting...")
    #     song = song[start:bookend*1000]

    #     out = qut_path / pod
    #     logger.info("Extracting...")
    #     song.export(out, format="mp3")

def overlay(track_1, track_2, out_path):
    """
    Overlay 2 given sound tracks
    WARNING: Order matters. Audio track length will be determined by the length of the first audio track.

    Args:
        file1 (Path or AudioSegment): give file path of audio or AudioSegment
        file2 (Path or AudioSegment): give file path of audio or AudioSegment
        out_path (Path or str): output path of created file.
    """

    # if sent items are not audiosegments, load em.

    if not isinstance(track_1, AudioSegment):
        logger.info("Loading track 1")
        track_1 = AudioSegment.from_file(track_1)
    if not isinstance(track_2, AudioSegment):
        logger.info("Loading track 2")
        track_2 = AudioSegment.from_file(track_2)

    combined = track_1.overlay(track_2)

    logger.info("Overlaying tracks")
    combined.export(out_path)
 
def load_tracks(track_path: Path):
    """
    Load tracks, return list.

    Args:
        path (Path): path to tracks

    Returns:
        list: loads tracks into audio segments and returns them
    """

    tracks = []

    clips = sorted(os.listdir(track_path))

    for clip in clips:
        tracks.append(AudioSegment.from_file(track_path / clip))

    logger.info("Done loading tracks.")
    return tracks

def generate_track(track_len: int, tracks: list):
    """
    Generate from given set of overlay track a new track thats smaller than
    or equal to the given pod.

    Args:
        track_len (int): expected length of pod.
        tracks (list): 

    Returns:
        tracks (AudioSegment): return newly created sedment.
    """

    logger.info(f"Pod length: {track_len}")

    # Shuffle tracks for adding to the pod.
    random.shuffle(tracks)

    generated_track = AudioSegment.silent(duration=15000)

    # In a loop, pop tracks one at a time till sum <= track_len 
    while True:
        lens = []
        for track in tracks:
            lens.append(track.duration_seconds)

        if sum(lens) >= track_len:
            tracks.pop()

        else:
            logger.info(f"Final Tracks length: {sum(lens)}, Tracks left: {len(tracks)}")
            break

    # Build track by adding upsegments!
    for track in tracks:
        generated_track += track
    
    # reduce volume by 30dB
    generated_track = generated_track - 30

    return generated_track

def main():
    """
    Main function.
    """

    logging.basicConfig(filename=CONFIG[SECTION]['log'],\
                    level=CONFIG[SECTION]['level'],\
                    format='%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s',\
                    datefmt='%Y-%m-%d %H:%M:%S')

    # This step is now done.
    # pool_extract(files)

    track_path = Path(Path.cwd()) / "data" / "napoleon" / "tracks"
    tracks = load_tracks(track_path)

    # in a for loop:
    podcasts = sorted(os.listdir(pod_path))
    for pod in podcasts:
        # Find lengths of ep.

        loaded_pod = AudioSegment.from_file(pod_path / pod)

        generated_track = generate_track(track_len=loaded_pod.duration_seconds, tracks=tracks)

        overlay(loaded_pod, generated_track, Path("/home") / "karan" / "q8ueato" / "pod" / pod)

        sys.exit()

    # Arrange all tracks in random order
    # get lengths and array them to fit inside ep.
    # Fade out on each end.

    # print(audio.duration_seconds)

if __name__ == "__main__":
    main()
