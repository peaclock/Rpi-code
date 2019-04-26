# ===================================================================
# Main code to make this clock work.
# ===================================================================

#import statements all necessary
from flask import Flask
from flask_ask import Ask, statement, convert_errors
import RPi.GPIO as GPIO
import threading
import thread
import time
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from urllib import urlretrieve
from urlparse import urljoin
from zipfile import ZipFile
import pytz

app = Flask(__name__)
ask = Ask(app, '/')

logging.getLogger("flask_ask").setLevel(logging.DEBUG)
#read link below to understand flask_ask
#https://flask-ask.readthedocs.io/en/latest/

#global variables
flag = 0 #flag = 1 if ticking, 0 if not
global nowTimeDelta
global curr
curr = timedelta(seconds=0)
global increment
increment = timedelta(seconds=35)
global maxTime
maxTime = timedelta(hours=12)

# Make the clock tick consistently to fit real time rotations.
def servo():
    global curr
    global increment
    global maxTime
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(12, GPIO.OUT)
    p = GPIO.PWM(12, 1) # 1 Hz frequency
    p.start(.1)
    p.ChangeDutyCycle(.1) # .1 duty cycle
    time.sleep(.01)
    curr = curr + increment
    if curr >= maxTime:
        curr = curr - maxTime
    p.stop()
    GPIO.cleanup() #reset all ports

# Complete however many rotations necessary in order to change the time to an international time.
def change_time():
    # calculate the difference in time
    # all time calculations were done with timedelta.
    # datetime objects are hard to calculate and do math with.
    global curr
    global maxTime
    global nowTimeDelta
    global flag
    new_time = nowTimeDelta
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(12, GPIO.OUT)
    p = GPIO.PWM(12, 50) # 50 Hz
    if new_time >= maxTime:
        new_time = new_time - maxTime
    diff = new_time - curr
    # timedelta has limited attributes to use for calculations.
    if diff.total_seconds() < 0:
        diff = timedelta(days = 0, seconds = 43200 + diff.total_seconds(), microseconds = 0) # 43200 seconds in 12 hours
    rotations = (float(diff.total_seconds()) / 3600.0)
    p.start(1)
    p.ChangeDutyCycle(1) # duty cycle = 1. This combination of PWM frequency and duty cycle makes the rotation fast.
    time.sleep(2.0725 * rotations) # number of seconds to make time wait so the ticks are aligned with real time.
    p.stop()
    GPIO.cleanup()
    curr = new_time
    flag = 1
    threading.Thread(target=tick_servo).start() # Restart the ticking thread since the rotations for a time change are
    #finished.

# function that calls servo()
# sleep is necessary to align it with real time
def tick_servo():
    global flag
    i = 0
    while flag == 1:
        servo()
        #time.sleep(2)
        time.sleep(float(3600 / 104) + 1)

# function to turn the clock on initially
@ask.intent('GpioIntent', mapping={'status': 'status'}) # ask.intent is necessary to grab status from Alexa
def gpio_status(status):
    global flag
    if status in ['on', 'high']:
        flag = 1
        threading.Thread(target=tick_servo).start() # thread to start basic ticking
        return statement('Turning clock on.')
    else:
        flag = 0
        return statement('Excuse me?')

cities = {} # empty dictionary to hold all cities
with open('tzdict.txt','r') as fh: # open textfile and grab all cities and their timezones
    line = fh.readline()
    while line:
        a = line.split()
        timezone = a[len(a) - 1]
        timezone_length = len(timezone)
        city_ = line[0:(len(line) - timezone_length - 2)]
        cities[city_] = timezone
        line = fh.readline()
fh.close()

@ask.intent('Timezone', mapping={'city': 'city'}) #ask.intent grabs a city from an Alexa request
def time_status(city):
    city = city.encode('ascii', 'ignore') #change city to ascii
    global flag
    global nowTimeDelta

    fmt = '%Y-%m-%d %H:%M:%S %Z%z' #format to return to Alexa
    now = datetime.now(pytz.timezone(cities[city]))
    nowObject = now.replace(tzinfo=None) # necessary calculations needed to get now in a timedelta object
    yr = nowObject.year
    dy = nowObject.day
    mnth = nowObject.month
    nowTimeDelta = nowObject - datetime(year=yr, month=mnth, day=dy)

    flag = 0
    threading.Thread(target=change_time).start() # thread to change the time with rotations inside change_time
    return statement('Current time in {} is {}'.format(city.encode('ascii', 'ignore'), now.strftime('%a %b %d %Y %I:%M %p')))

if __name__ == '__main__':
    port = 5000  # the custom port you want
    app.run(host='0.0.0.0', port=port)


def main():
    nowTimeDelta = timedelta(seconds = 11810)
    change_time()

if __name__ == '__main__':
    main()
