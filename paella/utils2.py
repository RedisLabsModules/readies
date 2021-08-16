
from __future__ import print_function
import sys
from subprocess import Popen, PIPE

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def sh(cmd, join=True):
    shell = isinstance(cmd, str)
    proc = Popen(cmd, shell=shell, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(err)
    if join:
        out = ' '.join(out.split("\n")).strip()
    return out
