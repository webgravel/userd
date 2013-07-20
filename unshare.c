#define _GNU_SOURCE
#include <sched.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <signal.h>
#include <stdio.h>

int unshare_mount() {
  return unshare(CLONE_NEWNS);
}

int unshare_pid() {
  return unshare(CLONE_NEWPID);
}

int unshare_uts() {
  return unshare(CLONE_NEWUTS);
}

int unshare_ipc() {
  return unshare(CLONE_NEWIPC);
}

int unshare_net() {
  return unshare(CLONE_NEWNET);
}
