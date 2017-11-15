#!/usr/bin/python

import re
import time
import Queue
import thread
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

LED_block = 17
LED_cache = 27
LED_forward = 22

GPIO.setup(LED_block, GPIO.OUT)
GPIO.setup(LED_cache, GPIO.OUT)
GPIO.setup(LED_forward, GPIO.OUT)

Q_blocks = Queue.Queue()
Q_caches = Queue.Queue()
Q_forwards = Queue.Queue()

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

def process_queues(q_obj, led):
    while(True):
        if time.time() - q_obj.get() < .2:
            GPIO.output(led, 1)
            time.sleep(.2)
            GPIO.output(led, 0)

thread.start_new_thread(process_queues, (Q_blocks, LED_block))
thread.start_new_thread(process_queues, (Q_caches, LED_cache))
thread.start_new_thread(process_queues, (Q_forwards, LED_forward))

try:
    for line in loglines:
        #print line
        if re.search(": forwarded ", line):
            Q_forwards.put(time.time())
        elif re.search(": cached ", line):
            Q_caches.put(time.time())
        elif re.search("gravity\.list.*is", line):
            Q_blocks.put(time.time())
except KeyboardInterrupt:
    GPIO.cleanup()
