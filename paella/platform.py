
from __future__ import absolute_import
import platform

class Platform:
    def __init__(self):
        self.os = platform.system().lower()
        dist = platform.linux_distribution()
        distname = dist[0].lower()
        self.os_ver = self.full_os_ver = dist[1]
        if self.os == 'linux':
            if distname == 'fedora' or distname == 'ubuntu' or  distname == 'debian' or distname == 'arch':
                pass
            elif distname == 'centos linux':
                distname = 'centos'
            elif distname.startswith('redhat'):
                distname = 'redhat'
            elif distname.startswith('suse'):
                distname = 'suse'
            else:
                Assert(False), "Cannot determine distribution"
            self.dist = distname
        elif self.os == 'darwin':
            self.os = 'macosx'
            self.dist = self.os
            mac_ver = platform.mac_ver()
            self.full_os_ver = mac_ver[0] # e.g. 10.14, but also 10.5.8
            self.os_ver = '.'.join(self.full_os_ver.split('.')[:2]) # major.minor
            # self.arch = mac_ver[2] # e.g. x64_64
        elif self.os == 'windows':
            self.dist = self.os
            self.os_ver = platform.release()
            self.full_os_ver = os.version()
        else:
            Assert(False), "Cannot determine OS"

        self.arch = platform.machine().lower()
        if self.arch == 'amd64' or self.arch == 'x86_64':
            self.arch = 'x64'

    def is_debian_compat(self):
        return self.dist == 'debian' or self.dist == 'ubuntu'
    
    def is_redhat_compat(self):
        return self.dist == 'redhat' or self.dist == 'centos'
    
    def report(self):
        print("This system is " + self.distname + " " + self.distver + ".\n")
