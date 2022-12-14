#!/usr/bin/env python3
"""Parses the FOURCC data in GPMF stream into fields"""
import json
import re

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
    "TMPC": "Device temperature"
}


def parse_values(key, value):
    if key[-1] in ["SIUN", "UNIT", "GPSA", "DVNM"]:
        return "deg, deg, m, m/s, m/s" if value == b'degdegm\x00\x00m/sm/s' else value.decode('latin-1')
    elif key[-1] in ["STMP", "ORIN", "ORIO"]:
        return int.from_bytes(value, "big")
    elif key[-1] in ["TSMP", "SCAL", "GPSP", "GPSF", "DVID"]:
        if type(value) is list:
            return value
        else:
            return int(value)
    elif key[-1] in ["TMPC"]:
        return float(value)
    elif key[-1] in ["MTRX", "ACCL", "GYRO", "SHUT", "WBAL", "WRGB", "ISOE", "UNIF", "GPS5", "IORI", "GRAV", "CORI"]:
        return value
    else:
        return str(value)


if __name__ == '__main__':
    import sys
    from extract import get_gpmf_payloads_from_file
    from parse import parse_value, recursive
    payloads, parser = get_gpmf_payloads_from_file(sys.argv[1])
    test_data = {}
    for gpmf_data, timestamps in payloads:
        data_entry = []
        for element, parents in recursive(gpmf_data):
            try:
                value = parse_value(element)
            except ValueError:
                value = element.data
            data_entry.append(([x.decode('latin-1') for x in list(parents)+[element.key]], value))
        test_data.update({str(timestamps): data_entry})
    test_data2 = []
    for (key, val) in test_data.items():
        test_data_a = [i for i, j in enumerate(val) if "STMP" in j[0]]
        test_data_b = [0] + test_data_a + [len(val)]
        test_data_c = list(zip(test_data_b[:-1], test_data_b[1:]))
        test_data_d = list(map(lambda x: val[x[0]: x[1]], test_data_c))
        test_data_e = {"Interval in ms": key} | {FOURCC_DEFINITIONS.get(x[0][-1], x[0][-1]): parse_values(x[0], x[1]) for x in test_data_d[0]} | {re.sub("[\(\[].*?[\)\]]", "", x[2][1].decode('latin-1')).strip(): {FOURCC_DEFINITIONS.get(y[0][-1], y[0][-1]): parse_values(y[0], y[1]) for y in x[:2]+x[3:]} for x in test_data_d[1:]}
        test_data2.append(test_data_e)
    with open(sys.argv[2], 'w', encoding="utf-8") as fp:
        fp.write(json.dumps(test_data2, indent=4, ensure_ascii=False))
    