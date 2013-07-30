#!/usr/bin/env python
import signal
import sys
import threading

sys.path.append('/gravel/pkg/gravel-common')

import gravelrpc
import os
import cmd_util
import userns

def signal_exit(*things):
    if worker.exiting:
        print 'force exit'
        os._exit(1)
    else:
        worker.exiting = True
        print 'exiting...'
        worker.exit()
        print 'exit.'
        os._exit(1)

class Handler(gravelrpc.RPCHandler):
    allow_fd_passing = True

    def method_start_user(self, uid):
        worker.start_user(uid)

    def method_stop_user(self, uid):
        worker.stop_user(uid)

    def method_exit(self):
        worker.exit()

    def method_attach(self, uid, cmd, _fds):
        fd0, fd1, fd2 = _fds
        worker.attach(uid, cmd, fd0, fd1, fd2)

class Worker(object):
    def __init__(self):
        signal.signal(signal.SIGTERM, signal_exit)
        signal.signal(signal.SIGINT, signal_exit)
        self.running = {}
        self.lock = threading.RLock()
        self.exiting = False

    def start_user(self, uid):
        with self.lock:
            if uid not in self.running:
                self.running[uid] = MyUserNS(uid)
                self.running[uid].start()

    def exit(self):
        with self.lock:
            for uid in self.running.keys():
                self.stop_user(uid)

    def stop_user(self, uid):
        with self.lock:
            userns = self.running[uid]
            del self.running[uid]
            userns.stop()

    def attach(self, uid, cmd, fd0, fd1, fd2):
        self.running[uid].attach(cmd, stdin=fd0, stdout=fd1, stderr=fd2)

class MyUserNS(userns.UserNS):
    def _setup_more_fs(self):
        init_file = self.dir + '/etc/init.sh'
        open(init_file, 'w').close()
        os.chmod(init_file, 0o755)

        cmd_util.run_hooks('/gravel/pkg/gravel-userd/setupfs.d', [str(self.uid), self.dir])

if __name__ == '__main__':
    worker = Worker()
    Handler.main('userd')
