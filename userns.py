import ctypes
import os
import tempfile
import time
import struct
import threading
from subprocess import check_call, call

binds = ['/usr', '/bin', '/sbin',
         '/lib', '/lib32', '/libx32', '/lib64']

_unshare = ctypes.CDLL('./unshare.so')
_libc = ctypes.CDLL('libc.so.6')

def errwrap(name, *args):
    func = getattr(_unshare, name)
    result = func(*args)
    if result != 0:
        raise OSError('call %s%r failed' % (name, args))

class UserNS(object):
    def __init__(self, uid, nick=None):
        self.uid = uid
        self.nick = nick or 'u%d' % uid
        assert isinstance(self.uid, int)
        self.init_pid = None
        self.netip = get_ip(uid * 4)
        self.gwip = get_ip(uid * 4 + 1)
        self.selfip = get_ip(uid * 4 + 2)
        print 'gw:', self.gwip, 'self:', self.selfip

    def start(self):
        threading.Thread(target=self.run).start()

    def stop(self):
        if self.init_pid:
            try:
                os.kill(self.init_pid, 15)
                time.sleep(0.5)
                os.kill(self.init_pid, 9)
            except OSError:
                pass

    def run(self):
        self._setup_pid_pipe()
        self._setup_init_pipe()
        self._setup_dir()
        self.child_pid = os.fork()
        if self.child_pid == 0:
            os.dup2(self._initin, 0)
            errwrap('unshare_net')
            self._setup_net_guest()
            self._stage1()
            os._exit(0)
        else:
            self._setup_net_host()
            self.init_pid = self._read_pid()
            print 'init pid:', self.init_pid
            os.wait()

        print 'run finished'

    def _wait_for_init(self):
        while self.init_pid is None:
            time.sleep(0.1)

    def _setup_pid_pipe(self):
        self._pidin, self._pidout = os.pipe()

    def _setup_init_pipe(self):
        self._initin, self._initout = os.pipe()

    def _read_pid(self):
        data = os.read(self._pidin, 8)
        return struct.unpack('!Q', data)[0]

    def _write_pid(self, pid):
        os.write(self._pidout, struct.pack('!Q', pid))
        os.close(self._pidout)

    def _stage1(self):
        self._setup_fs()
        if os.fork() == 0:
            errwrap('unshare_ipc')
            errwrap('unshare_uts')
            errwrap('unshare_mount')
            errwrap('unshare_pid')
            self.child_pid = os.fork()
            if self.child_pid == 0:
                self._stage2()
            else:
                self._write_pid(os.getpid())
                os.wait()
            os._exit(0)
        else:
            os.wait()
        self._cleanup()

    def _cleanup(self):
        try:
            os.rmdir(self.dir)
        except OSError:
            pass

    def _setup_dir(self):
        self.dir = tempfile.mkdtemp()
        print 'directory', self.dir

    def _stage2(self):
        self._setup_env()
        os.chroot(self.dir)
        os.chdir('/')
        os.setuid(self.uid)
        #os.execv('/bin/bash', ['/bin/bash'])
        os.execv('/usr/bin/python', ['/usr/bin/python', '/gravel/pkg/gravel-userd/init.py'])

    def _setup_fs(self):
        mount('-t', 'tmpfs', 'none', target=self.dir)

        target = self.dir + '/gravel/pkg/gravel-userd'
        os.makedirs(target)
        mount('--bind', os.getcwd(), target=target)

        for bind in binds:
            mount('--bind', bind, target=self.dir + '/' + bind)

        mount('-t', 'proc', 'procfs', target=self.dir + '/proc')

        os.mkdir(self.dir + '/dev')
        for dev in ['null', 'zero', 'tty']:
            check_call(['cp', '-a', '/dev/' + dev, self.dir + '/dev/' + dev])

        self._setup_etc()

        errwrap('unshare_mount')

    def _setup_etc(self):
        os.mkdir(self.dir + '/etc')

        with open(self.dir + '/etc/passwd', 'w') as f:
            f.write('root:x:0:0:root:/root:/bin/bash\n')
            f.write('{0}:x:{1}:0:user:/:/bin/bash\n'.format(self.nick, self.uid))

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

        # while device exists in current namespace
        while dev_exists('veth%d_c' % self.uid):
            check_call('ip link set veth%d_c netns %d' % (self.uid, self.child_pid),
                       shell=True)
            time.sleep(0.1)

        check_call('ifconfig veth%d %s/30 up' % (self.uid, self.gwip), shell=True)

    def _setup_net_guest(self):
        devname = 'veth%d_c' % self.uid
        while not dev_exists(devname):
            time.sleep(0.1)

        check_call('ip link set dev %s name host' % devname, shell=True)
        check_call('ifconfig lo 127.0.0.1/8 up', shell=True)
        check_call('ifconfig host %s/30 up' % self.selfip, shell=True)
        check_call('ip ro add default via %s' % self.gwip, shell=True)
        check_call('iptables -I INPUT -d 10.0.0.0/8 -j REJECT', shell=True)
        check_call('iptables -I INPUT -d %s/30 -j ACCEPT' % self.netip, shell=True)

def dev_exists(name):
    return call('ip link show %s >/dev/null 2>&1' % name, shell=True) == 0

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
    ns = UserNS(int(os.environ.get('NSUID', 1007)))
    ns.start()
    time.sleep(10)
    ns.stop()
