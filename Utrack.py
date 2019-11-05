#!/usr/bin/python3

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
# 0.3 improve the usage of Test_gps, better accuracy, Phonetrack upload, click package, auto import into activitytracker

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
import multiprocessing
import signal
from shutil import copyfile
import sqlite3

### Declaration
release = "0.3"
PERIOD = 2 #in seconds
PERIOD_phonetrack = round(20 / PERIOD) #estimate in seconds,
ACC = 25 #Accuracy in meters
GPS_LOG = "/tmp/Utrack_log.txt"
temp_file = "/tmp/Utrack_tmp.txt"
global i
i = 0
y = 0

parser = argparse.ArgumentParser(description='Utouch tracker options.')
parser.add_argument('--cloud', help="Add Phonetrack address to enable cloud recording, address type https://Cloudserver.org/apps/phonetrack/log/owntracks/c1eb6b15bc694e1127db6ac4/")
#parser.add_argument('-MLS', help="Allow to scan wifi around your device and capture the GPS location to populate the Mozilla Location Service database.able to scan wifi around your device and capture the GPS location to populate the Mozilla Location Service database.",action="store_true")
parser.add_argument('-d', help="create a debug file /tmp/Utrack_log.txt",action="store_true")
parser.add_argument('-activity', help="Auto import the trip to Activity tracker application",action="store_true")
#parser.add_argument('-info', help="Display realtime informaiton",action="store_true") <= consumme too much CPU.
args = parser.parse_args()

open(GPS_LOG, 'w').close()

# Format Phonetrack address
URL = ""
URL = args.cloud
URL_PARA = str(URL)+str(datetime.date.today())
if args.cloud:
    print("Cloud url: " + URL_PARA)
if args.d:
    print("verbosity turned on\n")

# Set GPX
gpx = gpxpy.gpx.GPX()
gpx_track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(gpx_track)
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

def PhoneTrack(latitude, longitude, ELEVATION):
    DATA = {"lat": latitude,
            "lon": longitude,
            "timestamp" : str(time.time()),
            "alt" : ELEVATION}
    HEADERS = {"Content-type": "application/x-www-form-urlencoded", 'User-Agent': 'Utouch'}
    try:
        r = requests.post(url=URL_PARA, data=DATA, headers=HEADERS, timeout=PERIOD_phonetrack*0.95)
        if r.status_code == 200:
             print("\n Position saved to " + URL_PARA[:-67])
             r.close()
             if args.d:
                 file1 = open("","a")
                 file1.write("phonetrack takes too long... let's kill it...")
                 file1.close()
    except KeyboardInterrupt:
        leave(gpx)
    except Exception:
        pass

def watch(fn, words):
    fp = open(fn, 'r')
    while True:
        new = fp.readline()
        # Once all lines are read this just returns ''
        # until the file changes and a new line appears
        if new:
            for word in words:
                if word in new:
                    yield (word, new)
        else:
            time.sleep(0.1)

def add_run(gpx_part,name,act_type,filename):
    conn = sqlite3.connect('/home/phablet/.local/share/activitytracker.cwayne18/activities.db')
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE if not exists activities
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,name text, act_date text, distance text,
                   speed text, act_type text,filename text,polyline text)""")
    sql = "INSERT INTO activities VALUES (?,?,?,?,?,?,?,?)"
    start_time, end_time = gpx_part.get_time_bounds()
    l2d = '{:.3f}'.format(gpx_part.length_2d() / 1000.)
    moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx_part.get_moving_data()
    maxspeed = 'Max speed: {:.2f}km/h'.format(max_speed * 60. ** 2 / 1000. if max_speed else 0)
    duration = '{:.2f}'.format(gpx_part.get_duration() / 60)
    print("-------------------------")
    print("Activity file transfered to: " + filename)
    print("\nTrip added to Activity Tracker.")
    print("-------------------------")
    try:
        cursor.execute(sql, [None, name,start_time,l2d,duration,act_type,filename,"NA"])
        conn.commit()
    except sqlite3.Error as er:
        print("-------------______---_____---___----____--____---___-----")
        print(er)
    conn.close()


def read_gps(p):
    global latitude
    global longitude
    global ACCURACY
    global ELEVATION
    latitude = str("")
    longitude = str("")
    ACCURACY = float(999)
    elevation_a = []
    ELEVATION = str("")
    try:
        fn = temp_file
        words = ['latitude', 'longtide','elevation','accuracy','stop tracking']
        for hit_word, hit_sentence in watch(fn, words):
            line = hit_sentence
            if re.search("^latitude", line):
                try:
                    lat = line.split()
                    if re.match(".\d+.\d+", lat[1]):
                        latitude = lat[1]
                    else:
                        subprocess.Popen(["truncate", "-s", "0", temp_file], shell=False)
                except KeyboardInterrupt:
                    leave(gpx)
                except:
                    pass
            if re.search("^longtide", line): #longtide bug in test_gps
                try:
                    long = line.split()
                    if re.match(".\d+.\d+", long[1]):
                        longitude = long[1]
                    else:
                        subprocess.Popen(["truncate", "-s", "0", temp_file], shell=False)
                except KeyboardInterrupt:
                    leave(gpx)
                except:
                    pass
            if re.search("^accuracy", line):
                try:
                    ACCURACY = line.split()
                    #print(ACCURACY)
                    if re.match("\d+.\d+", ACCURACY[1]):
                        ACCURACY = ACCURACY[1]
                        ACCURACY = float(ACCURACY)
                    else:
                        subprocess.Popen(["truncate", "-s", "0", temp_file], shell=False)
                except KeyboardInterrupt:
                    leave(gpx)
                except:
                    pass
            if re.search("stop tracking", line):
                file1 = open(GPS_LOG,"a")
                file1.write("restart test_gps\n")
                file1.close()
                p.kill()
                p = subprocess.Popen(["/usr/bin/sudo","/usr/bin/test_gps"], shell=False, stdout=log, stderr=log)
            if re.search("elevation", line):
                elevation_T = line.split()
                try :
                    elevation_T[1] = float(elevation_T[1])
                    elevation_a.append(elevation_T[1])
                except KeyboardInterrupt:
                    leave(gpx)
                except:
                    pass
            if 70 > ACCURACY > 0 and len(longitude) > 0 and len(latitude) > 0:
                for i in range(len(elevation_a)):
                    ELEVATION = int(sum(elevation_a[1:]) / float(len(elevation_a)))
                    if ELEVATION > 0:
                        file1 = open(GPS_LOG,"a")
                        file1.write(str(datetime.datetime.now()) + "   " + str(latitude) + " " + str(longitude) + "  " + str(ELEVATION) + "  " + str(ACCURACY)  + "==" + "\n")
                        file1.close()
                        return ELEVATION, longitude, latitude, str(ACCURACY)
    except KeyboardInterrupt:
        leave(gpx)

def leave(gpx):
    global info_display
    filename = str(round(time.time() * 1000))
    os.system('clear')
    print('\nGPX file Created : ' + filename + ".gpx")
    file = open("/home/phablet/Downloads/" + filename + ".gpx", "w+")
    file.write(gpx.to_xml())
    file.close()
    gpx_file = "/home/phablet/Downloads/" + filename + ".gpx"
    shutil.chown(gpx_file, user="phablet", group="phablet")
    gpx = gpxpy.parse(open(gpx_file))
    indentation = '   '
    info_display = ""
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
    if args.activity:
        newlocation="/home/phablet/.local/share/activitytracker.cwayne18/{}".format(filename + ".gpx")
        copyfile(gpx_file, newlocation)
        shutil.chown(newlocation, user="phablet", group="phablet")
        add_run(gpx,filename,"", newlocation)
    p.kill()
    sys.exit()

def Screen(latitude,longitude,ACCURACY):
    try:
        os.system('clear')
        screen_display = ''
        screen_display +="\n******************************************"
        screen_display +="\n****** UTouch GPS Tracking tool "+ str(release)+" ******"
        screen_display +="\n******************************************"
        screen_display +="\nTo stop select Ctrl+c on the virtual key"
        screen_display +="\n\nSetting: \n- Tracking period : " + str(PERIOD) +" s" + "\n- Recording accuracy max. required : " + str(ACC) +" m"
        if args.cloud:
            screen_display +="\n- Phonetrack server : " + URL_PARA[:-67]
            screen_display +="\n- Phonetrack Session : " + str(datetime.date.today())
            screen_display +="\n- Phonetrack period : " + str(PERIOD_phonetrack) + " s"
        if args.d:
            screen_display +="\n- Debug mode On"
        screen_display +="\n\nPosition No " + str(i)
        screen_display +="\n- Latitude  : " + latitude + "\n- Longitude : " + longitude + "\n- Accuracy  : " + str(round(float(ACCURACY)))
        print(screen_display)
        #if args.info: # to delete ?
        #    indentation = '- '
        #    info_display = ""
        #    length_2d = gpx.length_2d()
        #    length_3d = gpx.length_3d()
        #    info_display += "\n\nRealtime information:"
        #    info_display += "\n%sLength 2D: %s" % (indentation, format_long_length(length_2d))
        #    info_display += "\n%sLength 3D: %s" % (indentation, format_long_length(length_3d))
        #    moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx.get_moving_data()
        #    info_display += "\n%sMoving time: %s" %(indentation, format_time(moving_time))
        #    info_display += "\n%sStopped time: %s" %(indentation, format_time(stopped_time))
        #    info_display += "\n%sMax speed: %s" % (indentation, format_speed(max_speed))
        #    info_display += "\n%sAvg speed: %s" % (indentation, format_speed(moving_distance / moving_time) if moving_time > 0 else "?")
        #    print(info_display)
    except KeyboardInterrupt:
        leave(gpx)

def startup():
    time.sleep(1)
    os.system('clear')
    startup_screen = ""
    startup_screen +="\n******************************************"
    startup_screen +="\n****** UTouch GPS Tracking tool "+ str(release)+" ******"
    startup_screen +="\n******************************************"
    startup_screen +="\nThe tracking will start automatically."
    startup_screen +="\nTo close the application simply select Ctrl+c virtual key, the data will be automatically saved into a .gpx file named as per current timestamp."
    startup_screen +="\n\nWaiting for satellites\n\n"
    print(startup_screen)
try:
    log = open(temp_file, "w", 1)
    p = subprocess.Popen(["/usr/bin/sudo","/usr/bin/test_gps"], shell=False, stdout=log, stderr=log)
    startup()
    while True:
            if p.poll() == None:
                read_gps(p)
                time.sleep(PERIOD)
                Screen(latitude,longitude,ACCURACY)
                subprocess.Popen(["truncate", "-s", "0", temp_file], shell=False)
                if ACC > ACCURACY:
                        i = i + 1
                        y = y + 1
                        try:
                            latitude = float(latitude)
                            longitude = float(longitude)
                            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude, longitude, elevation=ELEVATION, time=datetime.datetime.now()))
                            file1 = open(GPS_LOG,"a")
                            file1.write(str(datetime.datetime.now()) + "   " + str(latitude) + " " + str(longitude) + "  " + str(ELEVATION) + "  " + str(ACCURACY)  + "<=" + "\n")
                            file1.close()
                        except KeyboardInterrupt:
                            leave(gpx)
                        except Exception:
                            pass
                        if y == PERIOD_phonetrack and args.cloud:
                            t = multiprocessing.Process(target=PhoneTrack, args=(latitude,longitude,ELEVATION))
                            t.start()
                            t.join(PERIOD_phonetrack*0.95)
                            if t.is_alive():
                                t.terminate()
                                t.join()
                            y = 0
            else:
                file1 = open(GPS_LOG,"a")
                file1.write("restart test_gps\n")
                file1.close()
                p.kill()
                p = subprocess.Popen(["/usr/bin/sudo","/usr/bin/test_gps"], shell=False, stdout=log, stderr=log)
except KeyboardInterrupt:
    leave(gpx)
