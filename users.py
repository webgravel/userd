import re
import graveldb
import gravelrpc
import cmd_util

PATH = '/gravel/system/node'

class User(graveldb.Table('users', PATH)):
    default = dict(nick=None, active=False)

    def setup(self):
        if not self.data.nick:
            self.data.nick = 'u%d' % self.name
        if not re.match('^[a-z0-9_-]+$', self.data.nick):
            raise ValueError('bad nick')

    def take(self):
        cmd_util.run_hooks('take.d', [str(self.name)])
        self.data.active = True
        self.save()

    def activate(self):
        if not self.data.active:
            raise ValueError('user not activated by master')

        cmd_util.run_hooks('activate.d', [str(self.name)])
        self._active_daemon()

    def _active_daemon(self):
        rpc = gravelrpc.Client('userd')
        rpc.start_user(self.name)
