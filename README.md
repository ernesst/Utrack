# Utrack

Background terminal position tracking for Ubuntu Touch devices.

## Download
[![OpenStore](https://open-store.io/badges/en_US.png)](https://open-store.io/app/utrack)

## Credits
- Thanks to gpx-py : https://github.com/tkrajina/gpxpy

## features
- Record into a gpx file your trip into Download folder,
- Auto-import trip into activitytracker,
- Realtime recording of your position into Phonetrack https://apps.nextcloud.com/apps/phonetrack

## version
- 0.3
  - Auto import into activitytracker
  - Realtime tracking into PhoneTrack
  - Harden and cleanup code
  - Better use of the binary test_gps
  - Add debug information
  - Add help menu
  - Renaming of the script
  - migrate to github
- 0.2 update UI
- 0.1 intial release

## Requierments
- Depending of the Ubuntu Touch version and AppArmor security, you might need to run this app into an iperspace. See https://open-store.io/app/iperspace.emanuelesorce Currently RC and Stable requires this tool.
- Terminal app has to be allowed to run in background with the app ubuntu tweak tool https://open-store.io/app/ut-tweak-tool.sverzegnassi. 


## Howto use it
To start the application, it's required to be in the folder of the python script and be launched with sudo.
By default Utrack creates a gpx file at the end of the run, for extra features argument needs to be passed to the script :
```
phablet@ubuntu-phablet:~$ cd /opt/click.ubuntu.com/utrack/current/
phablet@ubuntu-phablet:/opt/click.ubuntu.com/utrack/current$ sudo ./Utrack.py -h
usage: Utrack.py [-h] [--cloud CLOUD] [-d] [-activity]

Utouch tracker options.

optional arguments:
  -h, --help     show this help message and exit
  --cloud CLOUD  Add Phonetrack address to enable cloud recording, address
                 type https://Cloudserver.org/apps/phonetrack/log/owntracks/c1eb6b15bc694e1127db6ac4/
  -d             create a debug file /tmp/Utrack_log.txt
  -activity      Auto import the trip to Activity tracker application
```
Thus to record a gpx file + pushing it to Activitytracker the following is required : ```sudo ./Utrack.py -activity```
To record a gps file + Activitytracker + phonetrack :  ```sudo ./Utrack.py -activity --cloud https://Cloudserver.org/apps/phonetrack/log/owntracks/c1eb6b15bc694e1127db6ac4/```

## Userfriendly tip
- The application is located in the folder /opt/click.ubuntu.com/utrack/current/, in order to ovoid each time to write down this path, let's create a bash alias doing that for you.
- open ~/.bashrc by ```nano ~/.bashrc```
- add the following : ```alias GPS="cd /opt/click.ubuntu.com/utrack/current/ && sudo ./Utrack.py"```
- close the terminal and reopen it,
- To start the recording by calling the shortcut ```GPS```.

I've two alias one with the other without --cloud argument.

Enjoy.
