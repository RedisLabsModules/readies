#!/bin/sh
''''[ ! -z $VIRTUAL_ENV ] && exec python -u -- "$0" ${1+"$@"}; command -v python3 > /dev/null && exec python3 -u -- "$0" ${1+"$@"}; exec python2 -u -- "$0" ${1+"$@"} # '''

import sys
import os
import argparse

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
import paella

#----------------------------------------------------------------------------------------------

class SystemSetup(paella.Setup):
    def __init__(self, nop=False):
        paella.Setup.__init__(self, nop)

    def common_first(self):
        # self.install("")
        # self.group_install("")
        # self.setup_pip()
        # self.pip_install("")
        print("common_first")

    def debian_compat(self):
        print("debian_compat")

    def redhat_compat(self):
        print("redhat_compat")

    def fedora(self):
        print("fedora")

    def macos(self):
        print("macos")

    def common_last(self):
        print("common_last")

#----------------------------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Set up system for build.')
parser.add_argument('-n', '--nop', action="store_true", help='no operation')
# parser.add_argument('--bool', action="store_true", help="flag")
# parser.add_argument('--int', type=int, default=1, help='number')
# parser.add_argument('--str', type=str, default='str', help='string')
args = parser.parse_args()

SystemSetup(nop = args.nop).setup()
