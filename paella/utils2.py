
import sys
from subprocess import Popen, PIPE

def eprint(*args, **kwargs):
	print >> sys.stderr, ' '.join(map(lambda x: "%s" % x, args))

def sh(cmd):
    if not isinstance(cmd, list):
        cmd = cmd.split()
    return " ".join(Popen(cmd stdout=PIPE).communicate()[0].split("\n"))
