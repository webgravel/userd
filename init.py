#!/usr/bin/env python
import signal
import os
import time
import sys
import errno

def exit(*a):
    try:
        os.kill(-1, 15)
    except OSError:
        pass
    os._exit(0)

signal.signal(signal.SIGTERM, exit)

def reap_child(*a):
    try:
        while os.waitpid(-1, os.WNOHANG | os.WUNTRACED | os.WCONTINUED): pass
    except OSError as err:
        if err.errno != errno.ECHILD:
            print err

signal.signal(signal.SIGCHLD, reap_child)

try:
    while sys.stdin.read(1):
        pass
    #time.sleep(100000)
finally:
    exit()
