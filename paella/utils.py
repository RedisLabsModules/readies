
import sys
import inspect
import os.path

if sys.version_info > (3, 0):
    from .utils3 import *
else:
    from .utils2 import *

#----------------------------------------------------------------------------------------------

def current_filepath():
    return os.path.abspath(inspect.getfile(inspect.currentframe().f_back))

#----------------------------------------------------------------------------------------------

class Env:
    def __getitem__(self, key):
        if type(key) == tuple:
            v = os.getenv(key[0])
            default = key[1]
        else:
            v = os.getenv(key)
            default = ''
        if v is None or v == '':
            return default
        return v

    def __setitem__(self, key, val):
        os.environ[key] = val

    def get(self, key, default=''):
        return os.getenv(key, default)

#----------------------------------------------------------------------------------------------

def dict_to_nt(name, d):
    if not d:
         return namedtuple(name, {})()
    return namedtuple(name, d.keys())(**d)
