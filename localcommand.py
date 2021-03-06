#!/usr/bin/env python2.7
import sys
import os
import argparse

sys.path.append('/gravel/pkg/gravel-common')
sys.path.append('/gravel/pkg/gravel-node')

import cmd_util
import users
import gravelnode
import gravelrpc
import graveldb
from gravelrpc import FD

def action_activate():
    parser = argparse.ArgumentParser()
    parser.add_argument('uid', type=int)
    args = parser.parse_args()

    user = users.User(args.uid)
    user.activate()

def action_attach():
    parser = argparse.ArgumentParser()
    parser.add_argument('uid', type=int)
    parser.add_argument('--newpty', '-n', action='store_true',
                        help='Run program in screen instance to prevent it from stealing pty.')
    parser.add_argument('cmd', nargs='+')
    args = parser.parse_args()

    if args.newpty:
        args = ['screen', '--'] + sys.argv[0].split(' ') + [str(args.uid), '--'] + args.cmd
        os.execvp('screen', args)

    user = users.User(args.uid)
    user.activate()

    client = gravelrpc.Client('userd')
    client.attach(args.uid, args.cmd, _fds=[FD(0), FD(1), FD(2)])

def action_fetchall():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    path = '/gravel/system/nodecache'

    for name in os.listdir(path):
        shelf = graveldb.TDBShelf(path + '/' + name)
        with shelf:
            for key in shelf.keys():
                del shelf[key]

    gravelnode.master_call('pushallusers')

if __name__ == '__main__':
    cmd_util.chdir_to_code()
    cmd_util.main_multiple_action(globals())
