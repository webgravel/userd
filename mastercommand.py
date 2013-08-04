#!/usr/bin/env python2.7
import sys

sys.path.append('/gravel/pkg/gravel-common')

import cmd_util
import users
import sys
import gravelrpc
import argparse

def action_take():
    parser = argparse.ArgumentParser()
    parser.add_argument('uid', type=int)
    args = parser.parse_args()

    user = users.User(args.uid)
    custom_data = gravelrpc.bson.load(sys.stdin)
    user.take(custom_data)

def action_return():
    pass

if __name__ == '__main__':
    cmd_util.chdir_to_code()
    cmd_util.main_multiple_action(globals())
