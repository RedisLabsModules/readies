
import os
import sys
import re
import subprocess
import tempfile
import textwrap
from .platform import OnPlatform, Platform
from .error import *
import paella

GIT_LFS_VER = '2.12.1'
PIP_VER = '19.3.1'

#----------------------------------------------------------------------------------------------

class OutputMode:
    def __init__(self, x):
        lx = str(x).lower()
        if x == True or x == 1 or lx == "yes" or lx == "true":
            self.mode = "True"
        elif x == False or x == 0 or lx == "no" or lx == "false":
            self.mode = "False"
        elif lx == "on_error":
            self.mode = "on_error"
        else:
            raise Error("Wrong output mode: %s" % x)

    def __eq__(self, x):
        return self.mode == OutputMode(x).mode

    def __bool__(self):
        return self.mode == "True"

    def on_error(self):
        return self.mode == "on_error"

class Runner:
    def __init__(self, nop=False):
        self.nop = nop
        # self.has_sudo = sh('command -v sudo') != ''
        self.has_sudo = False

    def run(self, cmd, at=None, output="on_error", _try=False, sudo=False):
        output = OutputMode(output)
        if cmd.find('\n') > -1:
            cmds1 = str.lstrip(textwrap.dedent(cmd))
            cmds = filter(lambda s: str.lstrip(s) != '', cmds1.split("\n"))
            cmd = "; ".join(cmds)
        if self.has_sudo and sudo:
            cmd = "sudo " + cmd
        print(cmd)
        sys.stdout.flush()
        if self.nop:
            return
        if output != True:
            fd, temppath = tempfile.mkstemp()
            os.close(fd)
            cmd = "{{ {CMD}; }} >{LOG} 2>&1".format(CMD=cmd, LOG=temppath)
        if at is None:
            rc = subprocess.call(["bash", "-c", cmd])
        else:
            with cwd(at):
                rc = os.system(cmd)
        if rc > 0:
            if output != True:
                if output.on_error():
                    os.system("cat {}".format(temppath))
            eprint("command failed: " + cmd)
            sys.stderr.flush()
        if output != True:
            os.remove(temppath)
        if rc > 0 and not _try:
            sys.exit(1)
        return rc

    def has_command(self, cmd):
        return Runner.has_command(cmd)

    @staticmethod
    def has_command(cmd):
        return os.system("command -v " + cmd + " > /dev/null") == 0

#----------------------------------------------------------------------------------------------

class PackageManager(object):
    def __init__(self, runner):
        self.runner = runner

    @staticmethod
    def detect(platform, runner):
        if platform.os == 'linux':
            if platform.dist == 'fedora':  # also include centos 8
                return Dnf(runner)
            elif platform.is_debian_compat():
                return Apt(runner)
            elif platform.is_redhat_compat():
                return Yum(runner)
            elif platform.dist == 'suse':
                return Zypper(runner)
            elif platform.dist == 'arch':
                return Pacman(runner)
            else:
                raise self.Error("Cannot determine package manager for distibution %s" % platform.dist)
        elif platform.os == 'macos':
            return Brew(runner)
        elif platform.os == 'freebsd':
            return Pkg(runner)
        else:
            raise Error("Cannot determine package manager for OS %s" % platform.os)

    def run(self, cmd, at=None, output="on_error", _try=False, sudo=False):
        return self.runner.run(cmd, at=at, output=output, _try=_try, sudo=sudo)

    def has_command(self, cmd):
        return self.runner.has_command(cmd)

    def install(self, packs, group=False, output="on_error", _try=False):
        return False

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        return False

    def add_repo(self, repourl, repo="", output="on_error", _try=False):
        return False

    def update(self, output="on_error"):
        return False

#----------------------------------------------------------------------------------------------

class Yum(PackageManager):
    def __init__(self, runner):
        super(Yum, self).__init__(runner)

    def install(self, packs, group=False, output="on_error", _try=False):
        if not group:
            return self.run("yum install -q -y " + packs, output=output, _try=_try, sudo=True)
        else:
            return self.run("yum groupinstall -y " + packs, output=output, _try=_try, sudo=True)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        if not group:
            return self.run("yum remove -q -y " + packs, output=output, _try=_try, sudo=True)
        else:
            return self.run("yum group remove -y " + packs, output=output, _try=_try, sudo=True)

    def add_repo(self, repourl, repo="", output="on_error", _try=False):
        if not self.has_command("yum-config-manager"):
            return self.install("yum-utils")
        return self.run("yum-config-manager -y --add-repo {}".format(repourl), output=output, _try=_try, sudo=True)

#----------------------------------------------------------------------------------------------

class Dnf(PackageManager):
    def __init__(self, runner):
        super(Dnf, self).__init__(runner)

    def install(self, packs, group=False, output="on_error", _try=False):
        if not group:
            return self.run("dnf install -q -y " + packs, output=output, _try=_try, sudo=True)
        else:
            return self.run("dnf groupinstall -y " + packs, output=output, _try=_try, sudo=True)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        if not group:
            return self.run("dnf remove -q -y " + packs, output=output, _try=_try, sudo=True)
        else:
            return self.run("dnf group remove -y " + packs, output=output, _try=_try, sudo=True)

    def add_repo(self, repourl, repo="", output="on_error", _try=False):
        if self.run("dnf config-manager 2>/dev/null", output=output, _try=True):
            return self.install("dnf-plugins-core", _try=_try)
        return self.run("dnf config-manager -y --add-repo {}".format(repourl), output=output, _try=_try, sudo=True)

#----------------------------------------------------------------------------------------------

class Apt(PackageManager):
    def __init__(self, runner):
        super(Apt, self).__init__(runner)

        # prevents apt-get from interactively prompting
        os.environ["DEBIAN_FRONTEND"] = 'noninteractive'

    def install(self, packs, group=False, output="on_error", _try=False):
        return self.run("apt-get -qq install -y " + packs, output=output, _try=_try, sudo=True)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        return self.run("apt-get -qq remove -y " + packs, output=output, _try=_try, sudo=True)

    def add_repo(self, repo_url, repo="", output="on_error", _try=False):
        if not self.has_command("add-apt-repository"):
            self.install("software-properties-common")
        rc = self.run("add-apt-repository -y {URL}".format(URL=repo_url), output=output, _try=_try, sudo=True)
        self.run("apt-get -qq update", output=output, _try=_try, sudo=True)
        return rc

    def update(self, output="on_error"):
        return self.run("apt-get -qq update -y", output=output, sudo=True)

#----------------------------------------------------------------------------------------------

class Zypper(PackageManager):
    def __init__(self, runner):
        super(Zypper, self).__init__(runner)

    def install(self, packs, group=False, output="on_error", _try=False):
        return self.run("zypper --non-interactive install " + packs, output=output, _try=_try, sudo=True)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        return self.run("zypper --non-interactive remove " + packs, output=output, _try=_try, sudo=True)

    def add_repo(self, repo_url, repo="", output="on_error", _try=False):
        return self.run("zypprt addrepo {URL} {NAME}".format(URL=repo_url, NAME=repo), output=output, _try=_try, sudo=True)

#----------------------------------------------------------------------------------------------

class Pacman(PackageManager):
    def __init__(self, runner):
        super(Pacman, self).__init__(runner)

    def install(self, packs, group=False, output="on_error", _try=False):
        return self.run("pacman --noconfirm -S " + packs, output=output, _try=_try, sudo=True)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        return self.run("pacman --noconfirm -R " + packs, output=output, _try=_try, sudo=True)

    def add_repo(self, repourl, repo="", output="on_error", _try=False):
        return False

#----------------------------------------------------------------------------------------------

class Brew(PackageManager):
    def __init__(self, runner):
        super(Brew, self).__init__(runner)

        if os.getuid() == 0 and os.getenv("BREW_AS_ROOT") != "1":
            eprint("Cannot run as root. Set BREW_AS_ROOT=1 to override.")
            sys.exit(1)
        if sh('xcode-select -p') == '':
            eprint("Xcode tools are not installed. Please run xcode-select --install.")
            sys.exit(1)
        if 'VIRTUAL_ENV' not in os.environ:
            # required because osx pip installed are done with --user
            os.environ["PATH"] = os.environ["PATH"] + ':' + os.environ["HOME"] + '/Library/Python/2.7/bin'
        # this prevents brew updating before each install
        os.environ["HOMEBREW_NO_AUTO_UPDATE"] = "1"

    def install(self, packs, group=False, output="on_error", _try=False):
        # brew will fail if package is already installed
        rc = True
        for pack in packs.split():
            rc = self.run("brew list {PACK} &>/dev/null || brew install {PACK}".format(PACK=pack),
                     output=output, _try=_try) and rc
        return rc

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        rc = True
        for pack in packs.split():
            rc = self.run("brew remove {PACK}".format(PACK=pack), output=output, _try=_try) and rc
        return rc

    def add_repo(self, repourl, repo="", output="on_error", _try=False):
        return False

    def update(self, output="on_error"):
        if os.environ.get('BREW_UPDATE') != '1':
            return True
        return self.run("brew update || true", output=output)

#----------------------------------------------------------------------------------------------

class Pkg(PackageManager):
    def __init__(self, runner):
        super(Pkg, self).__init__(runner)

    def install(self, packs, group=False, output="on_error", _try=False):
        return self.run("pkg install -q -y " + packs, output=output, _try=_try, sudo=True)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        return self.run("pkg delete -q -y " + packs, output=output, _try=_try, sudo=True)

    def add_repo(self, repourl, repo="", output="on_error", _try=False):
        return False

#----------------------------------------------------------------------------------------------

class Setup(OnPlatform):
    def __init__(self, nop=False):
        OnPlatform.__init__(self)
        self.runner = Runner(nop)
        self.stages = [0]
        self.platform = Platform()
        self.os = self.platform.os
        self.arch = self.platform.arch
        self.osnick = self.platform.osnick
        self.dist = self.platform.dist
        self.ver = self.platform.os_ver
        self.repo_refresh = True

        self.package_manager = PackageManager.detect(self.platform, self.runner)

        self.python = sys.executable
        if re.match(r'Python 2', paella.sh(self.python + " --version 2>&1")):
            self.pyver = "2"
        else:
            self.pyver = "3"
        os.environ["PYTHONWARNINGS"] = 'ignore:DEPRECATION::pip._internal.cli.base_command'

    def setup(self):
        if self.repo_refresh:
            self.package_manager.update()
            self.python = paella.sh("command -v python" + self.pyver)

        self.invoke()

    def run(self, cmd, at=None, output="on_error", _try=False, sudo=False):
        return self.runner.run(cmd, at=at, output=output, _try=_try, sudo=sudo)

    @staticmethod
    def has_command(cmd):
        return Runner.has_command(cmd)

    #------------------------------------------------------------------------------------------

    def install(self, packs, group=False, output="on_error", _try=False):
        return self.package_manager.install(packs, group=group, output=output, _try=_try)

    def uninstall(self, packs, group=False, output="on_error", _try=False):
        return self.package_manager.uninstall(packs, group=group, output=output, _try=_try)

    def group_install(self, packs, output="on_error", _try=False):
        return self.install(packs, group=True, output=output, _try=_try)

    def add_repo(self, repo_url, repo="", _try=False):
        return self.package_manager.add_repo(repo_url, repo=repo, _try=_try)

    #------------------------------------------------------------------------------------------

    def pip_install(self, cmd, output="on_error", _try=False):
        pip_user = ''
        if self.os == 'macos' and 'VIRTUAL_ENV' not in os.environ:
            pip_user = '--user '
        return self.run(self.python + " -m pip install --disable-pip-version-check " + pip_user + cmd,
                        output=output, _try=_try, sudo=True)

    def setup_pip(self, output="on_error", _try=False):
        if self.run(self.python + " -m pip --version", _try=True, output=False) != 0:
            if sys.version_info.major == 3:
                # required for python >= 3.6, may not exist in prior versions
                self.install("python3-distutils", _try=True)
            self.install_downloaders()
            with_sudo = self.os != 'macos'
            pip_user = '--user' if self.os == 'macos' else ''
            self.run("wget -q https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py",
                     output=output, _try=_try)
            self.run(self.python + " /tmp/get-pip.py pip=={PIP_VER} {PIP_USER}".
                     format(PIP_VER=PIP_VER, PIP_USER=pip_user),
                     output=output, _try=_try, sudo=with_sudo)
            if sys.version_info.major == 3:
                self.pip_install("setuptools==49.3.0")

    #------------------------------------------------------------------------------------------

    def install_downloaders(self, _try=False):
        if self.os == 'linux':
            self.install("ca-certificates", _try=_try)
        self.install("curl wget", _try=_try)

    def install_git_lfs_on_linux(self, _try=False):
        if self.arch == 'x64':
            lfs_arch = 'amd64'
        elif self.arch == 'arm64v8':
            lfs_arch = 'arm64'
        elif self.arch == 'arm32v7':
            lfs_arch = 'arm'
        else:
            raise Error("Cannot determine platform for git-lfs installation")
        self.run("""
            set -e
            d=$(mktemp -d /tmp/git-lfs.XXXXXX)
            mkdir -p $d
            wget -q https://github.com/git-lfs/git-lfs/releases/download/v{LFS_VER}/git-lfs-linux-{ARCH}-v{LFS_VER}.tar.gz -O $d/git-lfs.tar.gz
            (cd $d; tar xf git-lfs.tar.gz)
            $d/install.sh
            rm -rf $d
            """.format(LFS_VER=GIT_LFS_VER, ARCH=lfs_arch))

    def install_gnu_utils(self, _try=False):
        packs = ""
        if self.os == 'macos':
            packs= "make coreutils findutils gnu-sed gnu-tar gawk"
        elif self.os == 'freebsd':
            packs = "gmake coreutils findutils gsed gtar gawk"
        self.install(packs)
        for x in ['make', 'find', 'sed', 'tar', 'mktemp']:
            p = "/usr/local/bin/{}".format(x)
            if not os.path.exists(p):
                self.run("ln -sf /usr/local/bin/g{} {}".format(x, p))
            else:
                eprint("Warning: {} exists - not replaced".format(p))

    def install_linux_gnu_tar(self, _try=False):
        if self.os != 'linux':
            eprint("Warning: not Linux - tar not installed")
            return
        if self.arch != 'x64':
            raise Error("Cannot install gnu tar on non-x64 platform")
        self.run("""
            dir=$(mktemp -d /tmp/tar.XXXXXX)
            (cd $dir; wget -q -O tar.tgz http://redismodules.s3.amazonaws.com/gnu/gnu-tar-1.32-x64-centos7.tgz; tar -xzf tar.tgz -C /; )
            rm -rf $dir
            """)

    def install_ubuntu_modern_gcc(self, _try=False):
        if self.dist != 'ubuntu':
            eprint("Warning: not Ubuntu - modern gcc not installed")
            return
        self.install("software-properties-common")
        self.run("add-apt-repository -y ppa:ubuntu-toolchain-r/test")
        self.install("gcc-7 g++-7")
        self.run("update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 60 --slave /usr/bin/g++ g++ /usr/bin/g++-7")
