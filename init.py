#!/usr/bin/env python
import signal
import os
import time
import sys
import errno
import passfd
import subprocess

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

sockfd = int(os.environ['SOCKFD'])
del os.environ['SOCKFD']

def recvfd(fd):
    while True:
        try:
            return passfd.recvfd(fd)
        except OSError as err:
            if err.errno == errno.EINTR:
                continue

while True:
    try:
        fd0, msg = recvfd(sockfd)
    except RuntimeError: # probably EOF
        break
    fd1, _ = recvfd(sockfd)
    fd2, _ = recvfd(sockfd)

    subprocess.Popen(msg.split('\0'),
                     stdin=fd0,
                     stdout=fd1,
                     stderr=fd2,
                     close_fds=1)

exit()
