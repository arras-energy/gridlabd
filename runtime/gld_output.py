"""GridLAB-D Output Streams"""

import os
import sys
from collections import namedtuple

import gldcore

class Options:

	def __init__(self,**kwargs):
		self._setdefault("modulename",kwargs,None)
		self._setdefault("verbose",kwargs,sys.stderr)
		self._setdefault("warning",kwargs,sys.stderr)

	def _setdefault(self,name,kwargs,default):
		setattr(self,name,kwargs[name] if name in kwargs else default)

options = Options(
	modulename=None,
	verbose=sys.stderr,
	warning=sys.stderr,
	)

def verbose(*args,**kwargs):
    """Output verbose message

    Arguments
    ---------
    - `args`: `print()` non-positional arguments
    - `kwargs`: `print()` positional arguments
    """
    if options.verbose:
        if not "file" in kwargs:
            kwargs["file"] = options.verbose
        print(f"VERBOSE  [{gldcore.get_global('clock')}] ({options.modulename}):", *args,**kwargs)

def warning(*args,**kwargs):
    """Output a warning message

    Arguments
    ---------
    - `args`: `print()` non-positional arguments
    - `kwargs`: `print()` positional arguments
    """
    if options.warning:
        if not "file" in kwargs:
            kwargs["file"] = options.warning
        print(f"WARNING  [{gldcore.get_global('clock')}] ({options.modulename}): ", *args,**kwargs)

