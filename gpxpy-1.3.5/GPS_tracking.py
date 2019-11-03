#!/usr/bin/env python3

#Copyright (C) 2019 Ernesst <ernesst@posteo.net>
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; version 3.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# 0.1 intial release
# 0.2 update UI
# 0.3 improve the usage of Test_gps, better accuracy

import time
import subprocess
import datetime
import re
import os
import sys
import shutil
import math as mod_math
import requests
sys.path.insert(0, "./gpxpy-1.3.5/")
import gpxpy
import gpxpy.gpx
import argparse

release = "0.3"
Freq = 2.5
#Freq_phonetrack = round(120 / Freq)
Freq_phonetrack = 5
i = 0
y = 0

# PhoneTrack server address:
parser = argparse.ArgumentParser()
parser.add_argument("Address", help="Add Phonetrack address to enable tracking", type=str,  nargs='?')
args = parser.parse_args()
URL = ""
URL = args.Address
URL_PARA = str(URL)+str(datetime.date.today())

print(URL_PARA)
gpx = gpxpy.gpx.GPX()
# Create first track in our GPX:
gpx_track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(gpx_track)

# Create first segment in our GPX track:
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

def format_time(time_s):
    if not time_s:
        return 'n/a'
    else:
        minutes = mod_math.floor(time_s / 60.)
        hours = mod_math.floor(minutes / 60.)
        return '%s:%s:%s' % (str(int(hours)).zfill(2), str(int(minutes % 60)).zfill(2), str(int(time_s % 60)).zfill(2))


def format_long_length(length):
    return '{:.3f}km'.format(length / 1000.)


def format_short_length(length):
    return '{:.1f}m'.format(length)

def format_speed(speed):
    if not speed:
        speed = 0
    else:
        return '{:.0f}m/s = {:.0f}km/h'.format(speed, speed * 3600. / 1000.)

def PhoneTrack(latitude, longitude, time, elevation):
    DATA = {"lat": latitude,
            "lon": longitude,
            "timestamp" : str(time.time()),
            "alt" : elevation}
    HEADERS = {"Content-type": "application/x-www-form-urlencoded", 'User-Agent': 'Utouch'}
    try:
        r = requests.post(url=URL_PARA, data=DATA, headers=HEADERS, timeout=1)
        if r.status_code == 200:
             print("\n Position saved to " + URL_PARA[:-67])
             r.close()
             r.close()
             time.sleep(2)
    except Exception:
        pass
    return

def read_gps(stdout):
    global latitude
    global longitude
    global accuracy
    global elevation
    latitude = str("")
    longitude = str("")
    accuracy = str("")
    elevation_a = []
    elevation = str("")
    for line in stdout:
        line = line.decode('utf-8')
        if re.search("^latitude", line):
            latitude = line.split()
            latitude = latitude[1]

        if re.search("^longtide", line): #longtide bug in test_gps
            longitude = line.split()
            longitude = longitude[1]

        if re.search("^accuracy", line):
            accuracy = line.split()
            accuracy = accuracy[1]

        if re.search("elevation", line):
            elevation_T = line.split()
            elevation_a.append(elevation_T[1])
        if accuracy != "":
            for i in range(len(elevation_a)):
                 elevation_a[i] = float(elevation_a[i])
            elevation = int(sum(elevation_a) / float(len(elevation_a)))
            return elevation, longitude, latitude

try:
    os.system('clear')
    #print(len(str(URL)))
    print("\n**********************************")
    print("** UTouch GPS Tracking tool "+ str(release) +" **")
    print("**********************************")
    print("The tracking will start automatically.")
    print("To close the application simply select Ctrl+c virtual key, the data will be automatically saved into a .gpx file named as per current timestamp.")
    print("\nWaiting for satelites")
    CMD = ['sudo test_gps']
    p = subprocess.Popen(CMD, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=True)
    while True:
        read_gps(p.stdout)
        os.system('clear')
       # print(len(str(URL)))
        print("\n**********************************")
        print("** UTouch GPS Tracking tool "+ str(release)+" **")
        print("**********************************")
        print("To close the application simply select Ctrl+c virtual key")
        print("\nSetting: \n- Tracking period : " + str(Freq) +" seconds")
        if len(str(URL)) > 10:
             print("- Phonetrack server : " + URL_PARA[:-67])
             print("- Phonetrack Session : " + str(datetime.date.today()))
             print("- Phonetrack frequency : " + str(Freq_phonetrack) + " seconds")
        print("\nPosition No " + str(i))
        print("- Latitude  : " + latitude + "\n- Longitude : " + longitude + "\n- Accuracy  : " + str(round(float(accuracy))))
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude, longitude, elevation=elevation, time=datetime.datetime.utcnow()))
        time.sleep(Freq)
        i = i + 1
        y = y + 1
        if y == Freq_phonetrack:
            if len(str(URL)) > 10:
                PhoneTrack(latitude,longitude,time,elevation)
                y = 0

except KeyboardInterrupt:
    filename = str(round(time.time() * 1000))
    os.system('clear')
    print('\nGPX file Created : ' + filename + ".gpx")
    file = open(filename + ".gpx", "w+")
    file.write(gpx.to_xml())
    file.close()
    gpx_file = filename + ".gpx"
    shutil.chown(gpx_file, user="phablet", group="phablet")
    gpx = gpxpy.parse(open(gpx_file))
    indentation = '   '
    info_display = ""
    """
    gpx_part may be a track or segment.
    """
    length_2d = gpx.length_2d()
    length_3d = gpx.length_3d()
    info_display += "\n%sLength 2D: %s" % (indentation, format_long_length(length_2d))
    info_display += "\n%sLength 3D: %s" % (indentation, format_long_length(length_3d))
    moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx.get_moving_data()
    info_display += "\n%sMoving time: %s" %(indentation, format_time(moving_time))
    info_display += "\n%sStopped time: %s" %(indentation, format_time(stopped_time))
    info_display += "\n%sMax speed: %s" % (indentation, format_speed(max_speed))
    info_display += "\n%sAvg speed: %s" % (indentation, format_speed(moving_distance / moving_time) if moving_time > 0 else "?")
    uphill, downhill = gpx.get_uphill_downhill()
    info_display += "\n%sTotal uphill: %s" % (indentation, format_short_length(uphill))
    info_display += "\n%sTotal downhill: %s" % (indentation, format_short_length(downhill))
    info_display += "\n\n\n"
    print(info_display)
    p.kill()
    sys.exit()
