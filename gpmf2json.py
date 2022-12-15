#!/usr/bin/env python3
"""Converts GoPro GPMF data to JSON"""
import json
import re
import os
from extract import get_gpmf_payloads_from_file
from parse import parse_value, recursive

FOURCC_DEFINITIONS = {
    "DVID": "Device/track ID",
    "DVNM": "Device name",
    "STRM": "Nested signal stream",
    "STNM": "Stream name",
    "RMRK": "Comments for any stream",
    "SCAL": "Scaling factor",
    "SIUN": "Standard Units",
    "UNIT": "Display units",
    "TYPE": "Typedefs for complex structures",
    "TSMP": "Total Samples delivered",
    "TIMO": "Time Offset",
    "EMPT": "Empty payload count",
    "ACCL": "3-axis accelerometer",
    "GYRO": "3-axis gyroscope",
    "ISOG": "Image sensor gain",
    "SHUT": "Exposure time",
    "GPS5": "GPS5",
    "GPSU": "UTC time and date",
    "GPSF": "GPS Fix",
    "GPSP": "GPS Precision",
    "STMP": "Microsecond timestamps",
    "MAGN": "Magnetometer",
    "FACE": "Face detection",
    "FCNM": "Faces counted per frame",
    "ISOE": "Sensor ISO",
    "ALLD": "Auto Low Light frame duration",
    "WBAL": "White Balance in Kelvin",
    "WRGB": "White Balance RGB gains",
    "YAVG": "Luma average",
    "HUES": "Predominant hues",
    "UNIF": "Image uniformity",
    "SCEN": "Scene classifier",
    "SROT": "Sensor Read Out Time",
    "CORI": "Camera Orientation",
    "IORI": "Image Orientation",
    "GRAV": "Gravity Vector",
    "WNDM": "Wind Processing",
    "MWET": "Microphone is wet",
    "AALP": "Audio Levels",
    "DISP": "Disparity track",
    "MAGN": "Magnetometer",
    "MSKP": "Main video frame skip",
    "LSKP": "Low res video frame skip",
    "GPS9": "GPS9",
    "TMPC": "Device temperature",
}


def is_valid_input(input_path, output_path):
    """checks if input is correct, provides user with feedback if this is not the case"""
    if not (input_path and output_path):
        print(
            'ERROR: two inputs are required.\nUse the format "python gpmf2json.py [input mp4/mov file] [output json file]" for a single file\nor  "python gpmf2json.py [input directory] [output directory]" for batch processing.'
        )
        return False
    if not os.path.exists(input_path):
        print(
            'ERROR: input file does not exist.\nUse the format "python gpmf2json.py [input mp4/mov file] [output json file]" for a single file\nor  "python gpmf2json.py [input directory] [output directory]" for batch processing.'
        )
        return False
    if input_path == output_path:
        print(
            'ERROR: input and output cannot be the same.\nUse the format "python gpmf2json.py [input mp4/mov file] [output json file]" for a single file\nor  "python gpmf2json.py [input directory] [output directory]" for batch processing.'
        )
        return False
    if not (os.path.isdir(input_path) == os.path.isdir(output_path)):
        print(
            'ERROR: please specify either two files or two directories as an input.\nUse the format "python gpmf2json.py [input mp4/mov file] [output json file]" for a single file\nor  "python gpmf2json.py [input directory] [output directory]" for batch processing.'
        )
        return False
    return True


def get_gpmf_data(infile):
    """utilizes python-gpmf code for extraction of GPMF data and puts it in dictionary"""
    payloads, _ = get_gpmf_payloads_from_file(infile)
    data = {}
    for gpmf_data, timestamps in payloads:
        data_entry = []
        for element, parents in recursive(gpmf_data):
            try:
                value = parse_value(element)
            except ValueError:
                value = element.data
            data_entry.append(
                ([x.decode("latin-1") for x in list(parents) + [element.key]], value)
            )
        data.update({str(timestamps): data_entry})
    return data


def cast_values(key, value):
    """casts values based on the datatype, which is determined by the last element in the key"""
    if key[-1] in ["SIUN", "UNIT", "GPSA", "DVNM"]:
        return (
            "deg, deg, m, m/s, m/s"
            if value == b"degdegm\x00\x00m/sm/s"
            else value.decode("latin-1")
        )
    elif key[-1] in ["STMP", "ORIN", "ORIO"]:
        return int.from_bytes(value, "big")
    elif key[-1] in ["TSMP", "SCAL", "GPSP", "GPSF", "DVID"]:
        if type(value) is list:
            return value
        else:
            return int(value)
    elif key[-1] in ["TMPC"]:
        return float(value)
    elif key[-1] in [
        "MTRX",
        "ACCL",
        "GYRO",
        "SHUT",
        "WBAL",
        "WRGB",
        "ISOE",
        "UNIF",
        "GPS5",
        "IORI",
        "GRAV",
        "CORI",
    ]:
        return value
    else:
        return str(value)


def process_gpmf_data(gpmf_data):
    """refines GPMF data and optimizes structure for usability with JSON file"""
    data = []
    for (key, val) in gpmf_data.items():
        data_a = [i for i, j in enumerate(val) if "STMP" in j[0]]
        data_b = [0] + data_a + [len(val)]
        data_c = list(zip(data_b[:-1], data_b[1:]))
        data_d = list(map(lambda x: val[x[0] : x[1]], data_c))
        data_e = (
            {"Interval in ms": key}
            | {
                FOURCC_DEFINITIONS.get(x[0][-1], x[0][-1]): cast_values(x[0], x[1])
                for x in data_d[0]
            }
            | {
                re.sub("[\(\[].*?[\)\]]", "", x[2][1].decode("latin-1")).strip(): {
                    FOURCC_DEFINITIONS.get(y[0][-1], y[0][-1]): cast_values(y[0], y[1])
                    for y in x[:2] + x[3:]
                }
                for x in data_d[1:]
            }
        )
        data.append(data_e)
    return data


def get_conv_files_list(input_path, output_path):
    """prepares list in [(input_path, output_path)] format for conversion"""
    if os.path.isdir(input_path):
        # converts list of mp4 or mov files in input files to list of (input_path, output_path) tuples
        return list(
            map(
                lambda x: (
                    os.path.join(input_path, x),
                    os.path.join(output_path, os.path.splitext(x)[0] + ".json"),
                ),
                filter(
                    lambda y: not os.path.isdir(y)
                    and os.path.splitext(y)[1].lower() in [".mp4", ".mov"],
                    os.listdir(input_path),
                ),
            )
        )
    else:
        return [(input_path, output_path)]


if __name__ == "__main__":
    import sys

    # gets user input, exit program if input is incorrect
    input_path = os.path.abspath(sys.argv[1])
    output_path = os.path.abspath(sys.argv[2])
    if not is_valid_input(input_path, output_path):
        exit()

    # prepares list in [(input_path, output_path)] format
    files = get_conv_files_list(input_path, output_path)

    # for each (input_path, output_path) pair, do conversion and write file
    for infile, outfile in files:
        data = process_gpmf_data(get_gpmf_data(infile))
        with open(outfile, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(data, indent=4, ensure_ascii=False))
