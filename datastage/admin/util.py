import errno
import os

def check_pid(*filenames):
    try:
        for filename in filenames:
            if not os.path.exists(filename):
                continue
            with open(filename) as f:
                pid = int(f.read().strip())
                break
        else:
            return False
        os.kill(pid, 0)
    except OSError, e:
        if e.errno == errno.ESRCH:
            return False
        raise
    else:
        return pid