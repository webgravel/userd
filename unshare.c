#define _GNU_SOURCE
#include <sched.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <signal.h>
#include <stdio.h>
#include <setjmp.h>

int unshare_mount() {
  return unshare(CLONE_NEWNS);
}

jmp_buf unshare_buf;

#define STACK_SIZE (1024 * 1024)
static char child_stack[STACK_SIZE];

int child_func(void* argp) {
  longjmp(unshare_buf, 1);
}

int fork_unshare_pid() {
  /**
   * I don't like this. clone(2) should be able to accept
   * NULL as childFunc.
   * Not portable (to HP-something, manpage says) and not
   * thread-safe.
   */
  if (setjmp(unshare_buf) != 0) {
    return 0;
  } else {
    pid_t pid;
    int result = clone(child_func,
                       child_stack + STACK_SIZE,
                       CLONE_NEWPID | SIGCHLD, &pid);
    if(result >= 0)
      return pid;
    else
      return result;
  }
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
