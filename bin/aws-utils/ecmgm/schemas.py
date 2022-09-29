from enum import Enum


class InstanceTypes(str, Enum):
    """
    Instance  vCPU*	Mem (GiB)
    t2.nano	    1	0.5
    t2.micro	1	1
    t2.small	1	2
    t2.medium	2	4
    t2.large	2	8
    t2.xlarge	4	16
    t2.2xlarge	8	32
    """

    nano = "t2.nano"
    micro = "t2.micro"
    small = "t2.small"
    medium = "t2.medium"
    large = "t2.large"
    xlarge = "t2.xlarge"
    doublelarge = "t2.2xlarge"


class InstanceArch(str, Enum):
    i386 = "i386"
    x86_64 = "x86_64"
    x86_64_mac = "x86_64_mac"
    arm64 = "arm64"


class OsImage(str, Enum):
    windows = "windows"
    ubuntu = "ubuntu"
    debian = "debian"
    suse = "suse"
    amazon_linux = "amazon_linux"
    redhat = "redhat"
    macos = "macos"


OS_SEARCH_MAPPING = {
    OsImage.windows: "*Windows*",
    OsImage.ubuntu: "*ubuntu*/images/*",
    OsImage.debian: "*debian",
    OsImage.suse: "*suse*",
    OsImage.amazon_linux: "amzn2-ami-hvm-*",
    OsImage.redhat: "*RHEL*",
    OsImage.macos: "*macos*",
}

OS_DEFAULT_USER_MAP = {OsImage.ubuntu: "ubuntu", OsImage.amazon_linux: "ec2"}
