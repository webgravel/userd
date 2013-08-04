import re
import graveldb
import gravelrpc
import cmd_util

PATH = '/gravel/system/node'

class User(graveldb.Table('users', PATH)):
    default = dict(nick=None, active=False, custom={}, old_custom={})

    def setup(self):
        if not self.data.nick:
            self.data.nick = 'u%d' % self.name
        if not re.match('^[a-z0-9_-]+$', self.data.nick):
            raise ValueError('bad nick')

    def take(self, custom_data):
        self.data.old_custom = self.data.custom
        self.data.custom = custom_data
        self.data.active = True
        self.save()
        cmd_util.run_hooks('updatecustom.d', [str(self.name)])

    def activate(self):
        if not self.data.active:
            raise UserNotActiveError('needs to be moved to this host by master')

        cmd_util.run_hooks('activate.d', [str(self.name)])
        self._activate_daemon()

    def _activate_daemon(self):
        rpc = gravelrpc.Client('userd')
        rpc.start_user(self.name)

class UserNotActiveError(Exception):
    pass
