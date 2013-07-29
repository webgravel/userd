gravel-userd
=============

Gravel user handling package for node. Puts user processes in sandbox.

Hooks
-----------

`setupfs.d` - executed just before running chroot as root, in target namespaces.
May write to `/etc/init.sh` which will be executed with target UID and chroot.
