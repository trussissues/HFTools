# HFTools
An open-source library for Human Factors research written in Python.

## Tools
The current version of HFTools only includes a system that shows visual/auditory warning based on customized conditions while connected to D-Lab (Ergoneers). The program was written in Python with external libraries such as PyGame. Installation of external libraries may be needed.

## Usage
Please make sure D-Lab is running and is sending AOI (Area-of-Interest) or other data via TCP/UDP before running the program. When ready, run *main.py* which a GUI window should pop-up. If the program is stuck, please check your TCP/UDP connection as lack of data input would result in freezing program.

The algorithm (logic) of showing warning is written in *warning_display.py*. A TCP/UDP socket can be created by calling methods in *input.py*. The built-in logger (*logger.py*) allows data-loggin for debugging and verification purposes. Please note that the time in logger uses the **system time**.