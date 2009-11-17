#
#  utils.py
#  wrapper
#
#  Created by max klymyshyn on 11/16/09.
#  Copyright (c) 2009 Sonettic. All rights reserved.
#

import os
import sys

def _doublequote(str):
    """
    Replace double quotes if it's necessary
    """
    return str.replace('"', '\\"')
        
def if_else(condition, a, b):
    """
    It's helper for lambda functions.
    """
    if condition: return a
    else: return b

def find_executable(executable, path=None):
    """Try to find 'executable' in the directories listed in 'path' (a
    string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH']).  Returns the complete filename or None if not
    found.
    
    There is from http://snippets.dzone.com/posts/show/6313
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
            
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None
        
