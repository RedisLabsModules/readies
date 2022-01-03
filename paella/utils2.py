
from __future__ import print_function
import sys
from subprocess import Popen, PIPE

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class ShError(Exception):
    def __init__(self, err, out=None, retval=None):
        super().__init__(err)
        self.out = out
        self.retval = retval

def sh(cmd, join=False, lines=False, fail=True):
    shell = isinstance(cmd, str)
    proc = Popen(cmd, shell=shell, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    out = out.strip()
    if lines is True:
        join = False
    if lines is True or join is not False:
        out = out.split("\n")
    if join is not False:
        s = join if type(join) is str else ' '
        out = s.join(out)
    if proc.returncode != 0 and fail is True:
        raise ShError(err, out=out, retval=proc.returncode)
    return out
