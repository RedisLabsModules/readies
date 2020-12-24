
import sys
from subprocess import Popen, PIPE

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def sh(cmd):
    # if not isinstance(cmd, list):
    #     cmd = cmd.split()
    # return " ".join(Popen(cmd, stdout=PIPE).communicate()[0].decode('utf-8').split("\n"))
    return " ".join(Popen(cmd, shell=True, stdout=PIPE).communicate()[0].decode('utf-8').split("\n"))
