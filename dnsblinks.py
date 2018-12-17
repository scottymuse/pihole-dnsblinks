#!/usr/bin/python

import re
import time
import Queue
import thread
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# LED pin definitions
LED_block = 17
LED_cache = 27
LED_forward = 22

# Pin setups
GPIO.setup(LED_block, GPIO.OUT)
GPIO.setup(LED_cache, GPIO.OUT)
GPIO.setup(LED_forward, GPIO.OUT)

# Initialize queues for threads
Q_blocks = Queue.Queue()
Q_caches = Queue.Queue()
Q_forwards = Queue.Queue()

# Setup log file generator
def dnsmasq_log_file_reader(logfile):
    logfile.seek(0,2)
    while True:
        line = logfile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

logfile = open("/var/log/pihole.log")
loglines = dnsmasq_log_file_reader(logfile)


# Function the queues will run to blink their lights
# The queues contain timestamps of when an event happened.
# The thread pulls those times off the queue and blinks the light.
# Since a lot of logs can come at once, just handle the recent ones,
# ignore the ones that may have shown up during the last blink.
def process_queues(q_obj, led):
    while(True):
        if time.time() - q_obj.get() < .2:
            GPIO.output(led, 1)
            time.sleep(.2)
            GPIO.output(led, 0)

# Start the threads
thread.start_new_thread(process_queues, (Q_blocks, LED_block))
thread.start_new_thread(process_queues, (Q_caches, LED_cache))
thread.start_new_thread(process_queues, (Q_forwards, LED_forward))

# Main loop.
# Read log file, do the regex for the log line we are looking for
# and add a time entry to the proper queue.
try:
    for line in loglines:
        #print line
        if re.search(": reply ", line):
            Q_forwards.put(time.time())
        elif re.search(": cached ", line):
            Q_caches.put(time.time())
        elif re.search(" is 0.0.0.0", line):
            Q_blocks.put(time.time())
except:
    print "Exiting"
finally:
    GPIO.cleanup()
