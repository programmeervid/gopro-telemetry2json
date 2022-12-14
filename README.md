# GoPro telemetry to JSON converter
Python program for converting ALL metadata contained in the GoPro GPMF stream to JSON

### Requirements
-   **Python** (tested on version 3.10.2)
-   **construct** module version 2.8.12 (does not work with latest version so make sure to run `pip install construct==2.8.12`)
-   **python-dateutil** module (tested on version 2.6.1)
-   **hachoir3** module (tested on version 3.0a2)

### How to run
-   For converting a single file, run `python gpmf2json.py [input mp4 file] [output json file]`.
-   For batch conversion, run `python gpmf2json.py [input directory] [output directory]`.
