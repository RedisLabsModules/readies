
from __future__ import absolute_import
import platform
import os
import re
from .text import match
from .files import fread
from .error import *

#----------------------------------------------------------------------------------------------

DEBIAN_VERSIONS = {
    'buzz':      '1.1',
    'rex':       '1.2',
    'bo':        '1.3',
    'hamm':      '2.0',
    'slink':     '2.1',
    'potato':    '2.2',
    'woody':     '3.0',
    'sarge':     '3.1',
    'etch':      '4.0',
    'lenny':     '5.0',
    'squeeze':   '6.0',
    'wheezy':    '7',
    'jessie':    '8',
    'stretch':   '9',
    'buster':   '10',
    'bullseye': '11',
    'bookworm': '12',
    'trixie':   '13',
}

UBUNTU_VERSIONS = {
    'trusty':  '14.04',
    'xenial':  '16.04',
    'bionic':  '18.04',
    'disco':   '19.04',
    'eoan':    '19.10',
    'focal':   '20.04',
    'groovy':  '20.10',
    'hirsute': '21.04',
}

MACOS_VERSIONS = {
    "cheetah":      "10.0",
    "puma":         "10.1",
    "jaguar":       "10.2",
    "panther":      "10.3",
    "tiger":        "10.4",
    "leopard":      "10.5",
    "snowleopard":  "10.6",
    "lion":         "10.7",
    "mountainlion": "10.8",
    "mavericks":    "10.9",
    "yosemite":     "10.10",
    "elcapitan":    "10.11",
    "sierra":       "10.12",
    "highsierra":   "10.13",
    "mojave":       "10.14",
    "catalina":     "10.15",
    "bigsur":       "11.0",
}

MACOS_VERSIONS_NICKS = {v: k for k, v in MACOS_VERSIONS.items()}

#----------------------------------------------------------------------------------------------

class Platform:

    class OSRelease():
        CUSTOM_BRANDS = [ 'elementary', 'pop' ]
        UBUNTU_BRANDS = [ 'elementary', 'pop' ]
        
        def __init__(self, brand=False):
            self.defs = {}
            self.brand_mode = brand
            with open("/etc/os-release") as f:
                for line in f:
                    try:
                        k, v = line.rstrip().split("=")
                        self.defs[k] = v.strip('"').strip("'")
                    except:
                        pass

        def __repr__(self):
            return str(self.defs)

        def is_custom_brand(self):
            id = self.defs.get("ID", "")
            return id != "" and id in self.CUSTOM_BRANDS

        #--------------------------------------------------------------------------------------

        def id(self):
            # e.g. "centos"
            if self.is_custom_brand() and not self.brand_mode:
                return self.id_like()
            return self.defs.get("ID", "")

        def id_like(self):
            # possibly list of values, e.g. "rhel fedora"
            like = self.defs.get("ID_LIKE", "").split()
            if like == []:
                return ""
            return like[0]

        def version_id(self):
            brand = self.brand_id()
            if brand in self.UBUNTU_BRANDS:
                ver_id = UBUNTU_VERSIONS.get(self.ubuntu_codename(), "")
                if ver_id == "":
                    raise Error("Cannot determine os version")
                return ver_id
                    
            ver = self.defs.get("VERSION_ID", "")
            if ver == "" and self.id() == 'debian':
                ver, _ = self.debian_sid_version()
            return ver

        def debian_sid_version(self):  # returns version_id, codename
            m = match(r'Debian GNU/Linux ([^/]+)/sid', self.pretty_name())
            if m:
                return DEBIAN_VERSIONS.get(m[1], ""), m[1]
            else:
                return "", ""
        
        def version_codename(self):
            brand = self.brand_id()
            if brand in self.UBUNTU_BRANDS:
                return self.ubuntu_codename()
            codename = self.defs.get("VERSION_CODENAME", "")
            if codename == "" and self.id() == 'debian':
                _, codename = self.debian_sid_version()
            return codename

        #--------------------------------------------------------------------------------------

        def variant_id(self):
            # fedora-specific
            return self.defs.get("VARIANT_ID")

        def ubuntu_codename(self):
            # ubuntu-specific
            return self.defs.get("UBUNTU_CODENAME")

        #--------------------------------------------------------------------------------------

        def name(self):
            return self.defs.get("NAME", "")

        def pretty_name(self):
            return self.defs.get("PRETTY_NAME", "")

        def version(self):
            # text
            return self.defs.get("VERSION", "")

        #--------------------------------------------------------------------------------------

        def brand_id(self):
            return self.defs.get("ID", "")

        def brand_codename(self):
            return self.defs.get("VERSION_CODENAME", "")

        def brand_version_id(self):
            return self.defs.get("VERSION_ID", "")

    #------------------------------------------------------------------------------------------

    def __init__(self, strict=False, brand=False):
        self.os = self.dist = self.os_ver = self.os_full_ver = self.osnick = self.arch = '?'
        self.strict = strict
        self.brand_mode = brand

        self.os = platform.system().lower()
        if self.os == 'linux':
            self._identify_linux()
        elif self.os == 'darwin':
            self._identify_macos()
        elif self.os == 'windows':
            self._identify_windows()
        elif self.os == 'sunos':
            self._identify_solaris()
        elif self.os == 'freebsd':
            self._identify_freebsd()
        else:
            if strict:
                raise Error("Cannot determine OS")
            self.os_ver = ''
            self.dist = ''

        self._identify_arch()

    #------------------------------------------------------------------------------------------

    def _identify_linux(self):
        try:
            os_release = Platform.OSRelease(brand=self.brand_mode)
            self.os_ver = os_release.version_id()
            self.osnick = self._identify_linux_osnick(os_release)
            self.dist = self._identify_linux_dist(os_release)
            self.os_full_ver = self._identify_linux_full_ver(os_release, self.dist)
        except:
            if strict:
                raise Error("Cannot determine distribution")
            self.os_ver = self.os_full_ver = 'unknown'

    def _identify_linux_full_ver(self, os_release, distname):
        if distname == 'centos' or distname == 'redhat':
            redhat_release = fread('/etc/redhat-release')
            m = match(r'.* release ([^\s]+)', redhat_release)
            if m:
                fullver = m[1]
                return fullver
        elif distname == 'ubuntu':
            brand = os_release.brand_id()
            if brand in os_release.UBUNTU_BRANDS:
                return self.os_ver
            m = match(r'([^\s]+)', os_release.version())
            if m:
                return m[1]
        return os_release.version_id()

    def _identify_linux_dist(self, os_release):
        distname = os_release.id()
        if distname == 'fedora' or  distname == 'debian' or distname == 'arch':
            pass
        elif distname == 'ubuntu':
            if self.osnick == 'ubuntu14.04':
                self.osnick = 'trusty'
        elif distname.startswith('centos'):
            distname = 'centos'
        elif distname.startswith('redhat') or distname == 'rhel':
            distname = 'redhat'
        elif distname.startswith('suse'):
            distname = 'suse'
        elif distname.startswith('amzn'):
            distname = 'amzn'
            self.osnick = 'amzn' + str(os_release.version_id())
        else:
            if self.strict:
                raise Error("Cannot determine distribution")
            elif distname == '':
                distname = 'unknown'
        return distname

    def _identify_linux_osnick(self, os_release):
        osnick = ""
        distname = os_release.id()
        if distname == 'ubuntu' or distname == 'debian':
            osnick = os_release.version_codename()
            if osnick == "":
                versions = DEBIAN_VERSIONS if distname == 'debian' else UBUNTU_VERSIONS
                versions_nicks = {v: k for k, v in versions.items()}
                osnick = versions_nicks.get(os_release.version_id(), "")
        if osnick == "":
            osnick = distname + str(os_release.version_id())
        return osnick

    #------------------------------------------------------------------------------------------

    def _identify_macos(self):
        self.os = 'macos'
        self.dist = ''
        mac_ver = platform.mac_ver()
        self.os_full_ver = mac_ver[0] # e.g. 10.14, but also 10.5.8
        self.os_ver = '.'.join(self.os_full_ver.split('.')[:2]) # major.minor
        self.osnick = MACOS_VERSIONS_NICKS.get(self.os_ver, self.os + str(self.os_full_ver.split('.')[1]))
        # self.arch = mac_ver[2] # e.g. x64_64

    def _identify_windows(self):
        self.dist = self.os
        self.os_ver = platform.release()
        self.os_full_ver = os.version()

    def _identify_freebsd(self):
        self.dist = ''
        ver = sh('freebsd-version')
        m = match(r'([^-]*)-(.*)', ver)
        self.os_ver = self.os_full_ver = m[1]
        self.osnick = self.os + self.os_ver

    def _identify_solaris(self):
        self.os = 'solaris'
        self.os_ver = ''
        self.dist = ''

    #------------------------------------------------------------------------------------------

    def _identify_arch(self):
        self.arch = platform.machine().lower()
        if self.arch == 'amd64' or self.arch == 'x86_64':
            self.arch = 'x64'
        elif self.arch == 'i386' or self.arch == 'i686' or self.arch == 'i86pc':
            self.arch = 'x86'
        elif self.arch == 'aarch64':
            self.arch = 'arm64v8'
        elif self.arch == 'armv7l':
            self.arch = 'arm32v7'

    #------------------------------------------------------------------------------------------

    def triplet(self):
        return '-'.join([self.os, self.osnick, self.arch])

    def is_debian_compat(self):
        return self.dist == 'debian' or self.dist == 'ubuntu' or self.dist == 'linuxmint'

    def is_redhat_compat(self):
        return self.dist == 'redhat' or self.dist == 'centos' or self.dist == 'amzn'

    def is_container(self):
        with open('/proc/1/cgroup', 'r') as conf:
            for line in conf:
                if re.search('docker', line):
                    return True
        return False

    def report(self):
        if self.dist != "":
            os = self.dist + " " + self.os
        else:
            os = self.os
        if self.osnick != "":
            nick = " (" + self.osnick + ")"
        else:
            nick = ""
        print(os + " " + self.os_ver + nick + " " + self.arch)

#----------------------------------------------------------------------------------------------

class OnPlatform:
    def __init__(self):
        self.stages = [0]
        self.platform = Platform()

    def invoke(self):
        os = self.os = self.platform.os
        dist = self.dist = self.platform.dist
        self.ver = self.platform.os_ver
        self.common_first()

        for stage in self.stages:
            self.stage = stage
            self.common()
            if os == 'linux':
                self.linux_first()
                self.linux()

                if self.platform.is_debian_compat():
                    self.debian_compat()
                if self.platform.is_redhat_compat():
                    self.redhat_compat()

                if dist == 'fedora':
                    self.fedora()
                elif dist == 'ubuntu':
                    self.ubuntu()
                elif dist == 'debian':
                    self.debian()
                elif dist == 'centos':
                    self.centos()
                elif dist == 'redhat':
                    self.redhat()
                elif dist == 'suse':
                    self.suse()
                elif dist == 'arch':
                    self.arch()
                elif dist == 'linuxmint':
                    self.linuxmint()
                elif dist == 'amzn':
                    self.amzn()
                else:
                    assert(False), "Cannot determine installer"

                self.linux_last()
            elif os == 'macos' or os == 'macos':
                self.macos()
            elif os == 'freebsd':
                self.freebsd()

        self.common_last()

    def common(self):
        pass

    def common_first(self):
        pass

    def common_last(self):
        pass

    def linux(self):
        pass

    def linux_first(self):
        pass

    def linux_last(self):
        pass

    def arch(self):
        pass

    def debian_compat(self): # debian, ubuntu, etc
        pass

    def debian(self):
        pass

    def centos(self):
        pass

    def fedora(self):
        pass

    def redhat_compat(self): # centos, rhel, amzn, etc
        pass

    def redhat(self):
        pass

    def ubuntu(self):
        pass

    def suse(self):
        pass

    def macos(self):
        self.macosx()

    def macosx(self):
        pass

    def windows(self):
        pass

    def bsd_compat(self):
        pass

    def freebsd(self):
        pass

    def linuxmint(self):
        pass

    def amzn(self):
        pass
