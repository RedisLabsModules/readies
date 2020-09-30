
import re
import textwrap

#----------------------------------------------------------------------------------------------

class RegexpMatch:
    def __init__(self, r, s):
        self.m = re.match(r, s)

    def __bool__(self):
        return bool(self.m)

    def __nonzero__(self):
        return bool(self.m)

    def __getitem__(self, k):
        return self.m.group(k)

def match(r, s):
    return RegexpMatch(r, s)

#----------------------------------------------------------------------------------------------

def heredoc(s):
    if s.find('\n') > -1:
        s = str.lstrip(textwrap.dedent(s))
    return s 
