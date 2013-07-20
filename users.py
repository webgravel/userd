import graveldb

PATH = '/gravel/system/master'

class User(graveldb.Table('users', PATH)):
    default = dict(nick=None)

    def setup(self):
        if not self.data.nick:
            self.data.nick = 'u%d' % self.name
        if not re.match('^[a-z0-9_-]+$', self.name):
            raise ValueError('bad nick')
