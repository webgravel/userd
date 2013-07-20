unshare.so: unshare.c
	gcc unshare.c -shared -fPIC -o unshare.so
