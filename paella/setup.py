
import paella
import os
import sys

#----------------------------------------------------------------------------------------------

def run(cmd):
    # rc = os.system(cmd)
    print(cmd)
    rc = 0
    if rc > 0:
        eprint("command failed: " + cmd)
        sys.exit(1)

def has_command(cmd):
    return os.system("command -v " + cmd + " > /dev/null") == 0

#----------------------------------------------------------------------------------------------

class Setup:
    def __init__(self):
        bb()
        self.stages = [0]
        self.platform = paella.Platform()

    def setup(self):
        os = self.os = self.platform.os
        dist = self.dist = self.platform.dist
        self.ver = self.platform.os_ver
        for stage in self.stages:
            self.stage = stage
            self.common()
            if os == 'linux':
                self.linux()
                if dist == 'fedora':
                    self.fedora()
                elif dist == 'ubuntu':
                    self.debian_compat()
                    self.ubuntu()
                elif dist == 'debian':
                    self.debian_compat()
                    self.debian()
                elif dist == 'centos':
                    self.redhat_compat()
                    self.centos()
                elif dist == 'redhat':
                    self.redhat_compat()
                    self.redhat()
                elif dist == 'suse':
                    self.suse()
                elif dist == 'arch':
                    self.arch()
                else:
                    Assert(False), "Cannot determine installer"
            elif os == 'macosx':
                self.osx()

    def common(self):
        pass

    def linux(self):
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

    def redhat_compat(self): # centos, rhel
        pass

    def redhat(self):
        pass
        
    def ubuntu(self):
        pass

    def suse(self):
        pass

    def macosx(self):
        pass

    def windows(self):
        pass

    def bsd_compat(self):
        pass

    def freebsd(self):
        pass

    #------------------------------------------------------------------------------------------

    def has_command(self, cmd):
        return os.system("command -v " + cmd + " > /dev/null") == 0

    #------------------------------------------------------------------------------------------

    def apt_install(self, packs, group=False):
        run("apt-get install -q -y " + packs)

    def yum_install(self, packs, group=False):
        if not group:
            run("yum install -q -y " + packs)
        else:
            run("yum groupinstall -y " + packs)

    def dnf_install(self, packs, group=False):
        if not group:
            run("dnf install -y " + packs)
        else:
            run("dnf groupinstall -y " + packs)

    def zypper_install(self, packs, group=False):
        run("zipper --non-interactive install " + packs)

    def pacman_install(self, packs, group=False):
        run("pacman --noconfirm -S " + packs)

    def brew_install(self, packs, group=False):
        run('brew install -y ' + cmd)

    def install(self, packs, group=False):
        if self.os == 'linux':
            if self.dist == 'fedora':
                self.dnf_install(packs, group)
            elif self.dist == 'ubuntu' or self.dist == 'debian':
                self.apt_install(packs, group)
            elif self.dist == 'centos' or self.dist == 'redhat':
                self.yum_install(packs, group)
            elif self.dist == 'suse':
                self.zypper_install(packs, group)
            elif self.dist == 'arch':
                self.pacman_install(packs, group)
            else:
                Assert(False), "Cannot determine installer"
        elif self.os == 'macosx':
            self.brew_install(packs, group)
        else:
            Assert(False), "Cannot determine installer"

    def group_install(self, packs):
        self.install(packs, group=True)

    #------------------------------------------------------------------------------------------

    def pip_install(self, cmd):
        run("pip install " + cmd)

    def pip3_install(self, cmd):
        run("pip3 install " + cmd)

    def setup_pip(self):
        get_pip = "set -e; cd /tmp; curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py"
        if not has_command("pip"):
            install("curl")
            run(get_pip + "; python2 get-pip.py")
        ## fails on ubuntu 18:
        # if not has_command("pip3") and has_command("python3"):
        #     run(get_pip + "; python3 get-pip.py")
