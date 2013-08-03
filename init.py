#!/usr/bin/env python
import signal
import os
import errno
import passfd
import subprocess
import traceback
import threading

def exit(*a):
    try:
        os.kill(-1, 15)
    except OSError:
        pass
    os._exit(0)

signal.signal(signal.SIGTERM, exit)

def reap_child(*a):
    try:
        while True:
            pid, exit = os.waitpid(-1, os.WNOHANG | os.WUNTRACED | os.WCONTINUED)
            if pid == 0:
                break
            if pid in managed_children:
                print 'managed child died (pid: %d)' % pid
                pipe = managed_children[pid]
                os.write(pipe, 'Y')
                del managed_children[pid]
    except OSError as err:
        if err.errno != errno.ECHILD:
            print err

signal.signal(signal.SIGCHLD, reap_child)

sockfd = int(os.environ['SOCKFD'])
del os.environ['SOCKFD']

managed_children = {}

def recvfd(fd):
    retry = 1000
    while True:
        try:
            return passfd.recvfd(fd)
        except OSError as err:
            retry -= 1
            if retry <= 0 or err.errno != errno.EINTR:
                raise

print 'init.py: PID', os.getpid()

if os.path.exists("/etc/init.sh"):
    subprocess.Popen(["bash", "/etc/init.sh"],
                     close_fds=1)

def starter(msg, fd0, fd1, fd2, wait_fd):
    try:
        popen = subprocess.Popen(msg.split('\0'),
                                 stdin=fd0,
                                 stdout=fd1,
                                 stderr=fd2,
                                 close_fds=1)
        managed_children[popen.pid] = wait_fd
    except:
        traceback.print_exc()
        os.write(wait_fd, 'E')


while True:
    try:
        fd0, msg = recvfd(sockfd)
    except RuntimeError: # probably EOF
        break
    fd1, _ = recvfd(sockfd)
    fd2, _ = recvfd(sockfd)
    wait_fd, _ = recvfd(sockfd)
    print 'starting process', [fd0, fd1, fd2, wait_fd], repr(msg)
    threading.Thread(target=starter, args=[msg, fd0, fd1, fd2, wait_fd]).start()

exit()
