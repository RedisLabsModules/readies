
import re

#----------------------------------------------------------------------------------------------

class RegexpMatch:
    def __init__(self, r, s):
        self.m = re.match(r, s)

    def __bool__(self):
        return bool(self.m)

    def __getitem__(self, k):
        return self.m.group(k)

def match(r, s):
    return RegexpMatch(r, s)

#----------------------------------------------------------------------------------------------
