import ctypes
import os
import tempfile
import time
from subprocess import check_call, call

binds = ['/usr', '/bin', '/sbin',
         '/lib', '/lib32', '/libx32', '/lib64']

_unshare = ctypes.CDLL('./unshare.so')

def errwrap(name, *args):
    func = getattr(_unshare, name)
    result = func(*args)
    if result != 0:
        raise OSError('call %s%r failed' % (name, args))

class UserNS(object):
    def __init__(self, uid):
        self.uid = uid
        assert isinstance(self.uid, int)
        self.gwip = get_ip(uid * 4 + 1)
        self.selfip = get_ip(uid * 4 + 2)
        print 'gw:', self.gwip, 'self:', self.selfip

    def start(self):
        self.child_pid = os.fork()
        if self.child_pid == 0:
            errwrap('unshare_net')
            self._setup_net_guest()
            self._stage1()
            os._exit(0)
        else:
            self._setup_net_host()
            os.wait()
        print 'start finished'

    def _stage1(self):
        self._setup_dir()
        if os.fork() == 0:
            errwrap('unshare_ipc')
            errwrap('unshare_uts')
            errwrap('unshare_mount')
            errwrap('unshare_pid')
            self.child_pid = os.fork()
            if self.child_pid == 0:
                self._stage2()
            else:
                os.wait()
            os._exit(0)
        else:
            os.wait()
        self._cleanup()

    def _cleanup(self):
        os.rmdir(self.dir)

    def _setup_dir(self):
        self.dir = tempfile.mkdtemp()

    def _stage2(self):
        self._setup_fs()
        self._setup_env()
        os.chroot(self.dir)
        os.chdir('/')
        os.execv('/bin/bash', ['/bin/bash'])

    def _setup_fs(self):
        mount('-t', 'tmpfs', 'none', target=self.dir)

        for bind in binds:
            mount('--bind', bind, target=self.dir + '/' + bind)

        mount('-t', 'proc', 'procfs', target=self.dir + '/proc')

        os.mkdir(self.dir + '/dev')
        for dev in ['null', 'zero', 'tty']:
            check_call(['cp', '-a', '/dev/' + dev, self.dir + '/' + dev])

        errwrap('unshare_mount')

    def _setup_env(self):
        for k in os.environ.keys():
            if k not in ['TERM']:
                del os.environ[k]

        os.environ.update(dict(
            PATH='/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'
        ))

    def _setup_net_host(self):
        call('ip link del veth{0} 2>/dev/null'.format(self.uid), shell=True)
        check_call('ip link add name veth{0} type veth peer name veth{0}_c'
                   .format(self.uid), shell=True)

        check_call('ip link set veth%d_c netns %d name host' % (self.uid, self.child_pid),
                   shell=True)
        check_call('ifconfig veth%d %s/30 up' % (self.uid, self.gwip), shell=True)

    def _setup_net_guest(self):
        while call('ip link show host &>/dev/null', shell=True) != 0:
            time.sleep(0.1)

        #check_call('ifconfig lo 127.0.0.1/8 up', shell=True)
        check_call('ifconfig host %s/30 up' % self.selfip, shell=True)
        check_call('ip ro add default via %s' % self.gwip, shell=True)

def mount(*args, **kwargs):
    assert len(kwargs) == 1
    target = kwargs['target']
    cmd = ['mount'] + list(args) + [target]
    if not os.path.exists(target):
        os.mkdir(target)
    check_call(cmd)

def get_ip(i):
    c = i % 256
    i /= 256
    b = i % 256
    i /= 256
    a = i % 256
    a = 128 + (a % 128)
    return '10.%d.%d.%d' % (a, b, c)

if __name__ == '__main__':
    UserNS(int(os.environ.get('NSUID', 1007))).start()
