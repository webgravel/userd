#!/usr/bin/env python
import signal
import sys
import threading

sys.path.append('/gravel/pkg/gravel-common')

import gravelrpc
import users
from userns import UserNS

def signal_exit(*things):
    worker.exit()

class Handler(gravelrpc.RPCHandler):
    def method_start_user(self, uid):
        pass

class Worker(object):
    def __init__(self):
        signal.signal(signal.SIGTERM, signal_exit)
        signal.signal(signal.SIGINT, signal_exit)
        self.running = {}
        self.lock = threading.Lock()

    def start_user(self, uid):
        with self.lock:
            if uid not in self.running:
                self.running[uid] = UserNS(uid)
                self.running[uid].run()

    def exit(self):
        pass

if __name__ == '__main__':
    worker = Worker()
    Handler.main('userd')
