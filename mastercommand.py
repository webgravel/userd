#!/usr/bin/env python2.7
import sys

sys.path.append('/gravel/pkg/gravel-common')

import cmd_util
import users
import argparse

def action_take():
    parser = argparse.ArgumentParser()
    parser.add_argument('uid', type=int)
    args = parser.parse_args()

    user = users.User(args.uid)
    user.take()

def action_return():
    pass

if __name__ == '__main__':
    cmd_util.chdir_to_code()
    cmd_util.main_multiple_action(globals())
