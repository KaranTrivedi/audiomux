#!./venv/bin/python

"""
Project for playing with audio files.
Merge audio files together, over lay them, etc.
"""
import configparser
import json
import logging
import os
import re
import sys
import random
import datetime

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
# TODO: Deal with the issue of most of the track being empty if the last track in random array if longer than rest of the pod.
# TODO: Parallel process to speed up there u can.

logger = logging.getLogger(SECTION)

# DEFINE PATHS HERE IN GIVEN FORMAT.
# Uses current dir as base path so be careful.

pod_path = Path(Path.cwd()) / "data" / CONFIG[SECTION]['folder'] / "pod"
edit_path = Path(Path.cwd()) / "data" / CONFIG[SECTION]['folder'] / "editted"
out_path = Path(Path.cwd()) / "data" / CONFIG[SECTION]['folder'] / "out"

def pool_extract():
    """
    Multi proc function to quickly process multiple tracks.
    """

    files = sorted(os.listdir(pod_path))

    with Pool(THREADS) as proc:
        print(proc.map(clip_audio, files))

def convert_to_seconds(time):
    """
    Convert hour:mins:seconds format to seconds.

    Args:
        time (string): Give time in format dd:hh:mm:ss

    Returns:
        float: total seconds in given timestamp.
    """

    modifier = (1, 60, 3600, 86400)

    times = [float(x) for x in time.split(":")][::-1]
    seconds = [times[i]*modifier[i] for i in range(len(times))]

    return sum(seconds)

def convert_to_humanreadable(time):
    """
    Convert time in seconds to human readable.

    Args:
        time (int or str): Send time in seconds.

    Returns:
        str: returns in format d days, hh:mm:ss
    """

    time = datetime.timedelta(seconds=float(time))

    # Going on a small detour here to reduce microseconds to only 3 places.
    time = str(time).split(".")

    if len(time) == 2:
        time[1] = time[1][:-3]

    return ".".join(time)

def find_tracks():

    timestamps = """
1. Richard Beddow - Napoleon Boneparte [0:01]
2. Richard Beddow - Corsica, Humble Beginings [2:14] 
3. Richard Beddow - Napoleon's Promise [3:19]
4. Richard Birdsall - Preparing the Arcole charge [4:47] 
5. Ian Livingstone - The Battle At Arcole [6:51]
6. Richard Birdsall - Naval Battle At St. Vincent [8:50] 
7. Richard Beddow - String Quintet I. Chamber Music I  [10:37]
8. Richard Beddow - String Quintet I. Chamber Music II [11:25]
9. Richard Beddow - String Quintet I. Chamber Music III [12:35]
10. Richard Birdsall - String Quintet II. Chamber Music IV [13:56]
11. Richard Beddow - Napoleon Heads to the East [14:44]
12. Ian Livingstone - Planning the Alexandria Invasion [16:02]
13. Richard Beddow - The Mamluks Attack [18:08]
14. Simon Ravn - Desert Preparations [20:27]
15. Richard Birdsall - The Battle of the Pyramids [22:29]
16. Richard Beddow - From Egypt to France [24:34]
17. Richard Beddow - The Art of War [25:17]
18. Richard Beddow - Choral Music I. a Cappella  [26:58]
19. Richard Birdsall - Choral Music II. a Cappella [27:43]
20. Richard Beddow - Choral Music III. a Cappella [28:38]
21. Ian Livingstone - Choral Music IV. a Cappella [29:38]
22. Richard Beddow - Threat of Naval Conflict [30:28]
23. Richard Beddow - HMS Victory [32:51]
24. Richard Birdsall - The Napoleonic Code [35:11] 
25. Simon Ravn - The Battle At Austerlitz [36:13]
26. Ian Livingstone - Naval Strike At Aix Roads [38:08]
27. Richard Birdsall - Napoleon's Ambition [40:21]
28. Ian Livingstone - String Quintet II. Chamber Music I [40:59] 
29. Ian Livingstone - String Quintet II. Chamber Music II [41:43]
30. Ian Livingstone - String Quintet II. Chamber Music III [42:29]
31. Richard Birdsall - String Quintet II. Chamber Music IV [43:17]
32. Richard Birdsall - Napoleon Plans Waterloo [44:02]
33. Richard Beddow - The Fields of War [46:24]
34. Richard Birdsall - Waterloo [48:36]
35. Simon Ravn - The Defeat At Waterloo [50:42] 
36. Richard Beddow - The End [51:40]
    """

    pattern = r"[0-9]\w+\. (.*-.*) \[(.*)\]"
    tracks = re.findall(pattern, timestamps, re.MULTILINE)

    for track in tracks:
        logger.info(f"{track[0]} : {convert_to_seconds(track[1])}.")
    # Use the convert to seconds function. Convert main track to seconds.
    # track -= length of each track. 
    # Publish all to tracks folder.

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
    length = 0

    # clips = sorted(os.listdir(track_path))
    clips = sorted(os.listdir(track_path))

    for clip in clips:
        tracks.append(AudioSegment.from_file(track_path / clip))

    logger.info("Done loading tracks.")
    for track in tracks:
        length += track.duration_seconds

    logger.info(f"{len(tracks)} Tracks found, "\
        f"tracks length: {convert_to_humanreadable(length)}")

    return tracks

def generate_track(track_len: int, track_dBFS: float, tracks: list):
    """
    Generate from given set of overlay track a new track thats smaller than
    or equal to the given pod.

    Args:
        track_len (int): expected length of pod.
        tracks (list): 

    Returns:
        tracks (AudioSegment): return newly created sedment.
    """

    logger.info(f"Pod length: {convert_to_humanreadable(track_len)}")

    # Shuffle tracks for adding to the pod.
    tmp_tracks = random.sample(tracks, len(tracks))

    generated_track = AudioSegment.silent(duration=30000)

    # In a loop, pop tracks one at a time till sum <= track_len 
    while True:
        # If there is only 1 track, no point in shuffling and adding.
        if len(tmp_tracks) == 1:
            logger.info(f"Track length: {convert_to_humanreadable(tmp_tracks[0].duration_seconds)}")
            break

        lens = []
        for track in tmp_tracks:
            lens.append(track.duration_seconds)

        if sum(lens) >= track_len:
            tmp_tracks.pop()

        else:
            logger.info(f"Final Tracks length: {convert_to_humanreadable(sum(lens))}"\
                f" Tracks left: {len(tmp_tracks)}")
            break

    # Build track by adding upsegments!
    for track in tmp_tracks:
        generated_track += track

    # reduce volume by configured dB, below main audio.
    loudness = track_dBFS - float(CONFIG[SECTION]['db'])

    logger.debug(f"Track loudness: {generated_track.dBFS:.3f}, "\
        f"Pod loudness: {track_dBFS:.3f}")
    logger.debug(f"Target loudness: {loudness:.3f}, "\
        f"Lower by: {float(CONFIG[SECTION]['db']):.3f}")

    generated_track = match_target_amplitude(generated_track, loudness)
    logger.debug(f"New Track loudness: {generated_track.dBFS:.3f}")

    return generated_track

def match_target_amplitude(sound, target_dBFS):
    """
    Adjust amplitude of soundtrack to given DB.

    Args:
        sound (audiosegment): Audio segment
        target_dBFS (float): decibels you would like to set the track to.

    Returns:
        (audiosegment): modified Audio segment
    """

    change_in_dBFS = target_dBFS - sound.dBFS
    logger.debug(f"Track loudness: {sound.dBFS}, Expected: {target_dBFS}")
    sound = sound.apply_gain(change_in_dBFS)
    logger.debug(f"New Track loudness: {sound.dBFS}")

    return sound

def normalize(tracks):
    """
    Normalize the loudness of all tracks to the quitest one.

    Args:
        tracks (list): List of audio segments

    Returns:
        (list): List of normalized audio segments
    """
    normalized_tracks = []
    dbs = []

    for track in tracks:
        dbs.append(track.dBFS)

    lowest = min(dbs)
    logger.debug(f"Quitest track at: {lowest}")

    for track in tracks:
        logger.debug(f"Track loudness: {track.dBFS}")
        normalized = match_target_amplitude(track, lowest)
        logger.debug(f"Track Normalized: {normalized.dBFS}")
        normalized_tracks.append(normalized)

    return normalized_tracks

def process_logic():
    """
    ################################################################
    ################################################################
    ################################################################
    process logic loop
    ################################################################
    ################################################################
    ################################################################
    """

    # This step is now done.
    # pool_extract(files)

    logger.info("Starting #########################################")

    logger.info("Loading tracks.")
    track_path = Path(Path.cwd()) / "data" / CONFIG[SECTION]['folder'] / "tracks"
    tracks = load_tracks(track_path)

    logger.info("Normalizing track volumes.")
    normalized_tracks = normalize(tracks)

    # Loading pods.
    # in a for loop:
    podcasts = sorted(os.listdir(pod_path))

    for pod in podcasts:
        # Find lengths of ep.

        logger.info(f"Loading pod {pod}")
        loaded_pod = AudioSegment.from_file(pod_path / pod)
        logger.info(f"Pod loudness: {loaded_pod.dBFS}")

        generated_track = generate_track(track_len=loaded_pod.duration_seconds,\
            track_dBFS=loaded_pod.dBFS,\
            tracks=normalized_tracks)

        overlay(loaded_pod, generated_track, out_path / pod)

    logger.info("Done #########################################")

    # Arrange all tracks in random order
    # get lengths and array them to fit inside ep.
    # Fade out on each end.

    # print(audio.duration_seconds)
    ################################################################
    ################################################################
    ################################################################
    # Process logic
    ################################################################
    ################################################################
    ################################################################

def main():
    """
    Main function.
    """

    logging.basicConfig(filename=CONFIG[SECTION]['log'],\
                    level=CONFIG[SECTION]['level'],\
                    format='%(asctime)s::%(levelname)s::%(name)s::%(funcName)s::%(message)s',\
                    datefmt='%Y-%m-%d %H:%M:%S')

    process_logic()
    # find_tracks()

    # Try to load one y axis.
    # print(track_path / clips[0])
    # print(AudioSegment.from_file(track_path / clips[0]).split_to_mono()[0])
    # sys.exit()

if __name__ == "__main__":
    main()
