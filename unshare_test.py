import userns, os

if userns.errwrap('fork_unshare_pid') == 0:
	print ('child:', os.getpid(), os.getppid())
else:
	print ('parent:', os.getpid(), os.getppid())
