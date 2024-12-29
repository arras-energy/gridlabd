"""Tool framework"""
import os
import sys
import io
import json
import math
from collections import namedtuple
import subprocess
import unitcalc
from typing import TypeVar
import inspect
import traceback

VERBOSE=False # enable verbose output to stderr
QUIET=False # quiet error output to stderr
WARNING=True # enable warning output to stderr
DEBUG=False # enable debug/traceback output to stderr
SILENT=False # disable output to stdout

E_OK = 0 # no error
E_SYNTAX = 1 # syntax error
E_INVALID = 2 # invalid argument/file
E_MISSING = 3 # missing argument/file
E_BADVALUE = 4 # bad value
E_INTERRUPT = 8 # interrupted
E_EXCEPTION = 9 # exception raised

def read_stdargs(argv):

    result = []
    for arg in list(argv[1:]):
        if arg in ["--debug"]:
            DEBUG = True
            argv.remove(arg)
        elif arg in ["--verbose"]:
            VERBOSE = True
            argv.remove(arg)
        elif arg in ["--quiet"]:
            QUIET = True
            argv.remove(arg)
        elif arg in ["--silent"]:
            SILENT = True
            argv.remove(arg)
        elif arg in ["--warning"]:
            WARNING = False
            argv.remove(arg)
        elif "=" in arg:
            key,value = arg.split("=",1)
            result.append((key,value.split(",")))
        else:
            result.append((arg,[]))

    return result

def output(*msg,**kwargs):
    if not SILENT:
        print(*msg,file=sys.stdout,**kwargs)

def exception(exc):
    if isinstance(exc,str):
        exc = MapError(exc)
    raise exc

def error(msg:str,code:[int|None]=None,**kwargs):
    if not QUIET:
        if code:
            print(f"ERROR [{os.path.basename(sys.argv[0])}]: {msg} (code {repr(code)})",file=sys.stderr,**kwargs)
        else:
            print(f"ERROR [{os.path.basename(sys.argv[0])}]: {msg}",file=sys.stderr,**kwargs)
    if DEBUG:
        raise MappingError(msg)
    if not code is None:
        sys.exit(code)

def verbose(msg,**kwargs):
    if VERBOSE:
        print(f"VERBOSE [{os.path.basename(sys.argv[0])}]: {msg}",file=sys.stderr,**kwargs)

def warning(msg,**kwargs):
    if WARNING:
        print(f"WARNING [{os.path.basename(sys.argv[0])}]: {msg}",file=sys.stderr,**kwargs)

def debug(msg,**kwargs):
    if DEBUG:
        print(f"DEBUG [{os.path.basename(sys.argv[0])}]: {msg}",file=sys.stderr,**kwargs)

def gridlabd(*args, bin=True, **kwargs):
    """Simple gridlabd runner"""
    if not "capture_output" in kwargs:
        kwargs["capture_output"] = True
    try:
        return subprocess.run(
            ["gridlabd.bin" if bin else "gridlabd"] + list(args), **kwargs
        )
    except:
        return None

def open_json(file,tmp=None,init=False):
    if tmp is None:
        tmp = "/tmp"
    outfile = os.path.join(tmp,os.path.splitext(os.path.basename(file))[0]+".json")
    result = gridlabd("-I" if init else "-C",file,"-o",outfile)
    if result.returncode != 0:
        raise RuntimeError("GLM conversion to JSON failed")
    return open(outfile,"r")

def version():
    """Get gridlabd version"""
    _version = gridlabd("--version")
    return _version.stdout.decode('utf-8').strip() if _version and _version.returncode==0 else ""

def double_unit(x:str):
    """Convert a string with unit to a float"""
    return float(x.split(" ",1)[0])

def integer(x:str):
    """Convert a string to an integer"""
    return int(x)

def complex_unit(x:str,
        form:str=None,
        prec:str=2,
        unit:str=None) -> [str|float|tuple[float]|complex]:
    """Convert complex value with unit

    Arguments:

    * `form` (str|None): formatting (default is None). Valid values are
      ('i','j','d','r','rect','mag','arg','ang','conjugate','real','imag','unit','str')

    * `prec` (int): precision (default is 2)

    * `unit` (str|None): unit to convert to (default is None)

    Returns:

    float: value (if form is 'mag','arg','ang','real','imag')

    str: formatted string (if form is 'i','j','d','r','unit','str')

    tuple[float]: tuple (if form is 'rect')
    
    complex: complex value (if form is 'conjugate' or None)
    """
    if form is str:
        return x
    z,u = x.split(" ",1)
    if form == "unit":
        return u
    z = complex(z)
    if form is None:
        return z

    # string formats
    x,y = round(z.real,prec),round(z.imag,prec)
    if form in ['i','j']:
        return f"{x:f}{y:+f}{form}"        
    if form == 'd':
        zm = round(abs(x),prec)
        za = round(math.atan2(x,y)*180/3.1416,prec)
        return f"{zm}{za:1f}d"
    if form == 'r':
        zm = round(abs(x),prec)
        za = round(math.atan2(x,y),prec)
        return f"{zm}{za:+f}r"

    # numerical formats
    if form == 'rect':
        return z.real,z.imag
    if form == 'mag':
        return abs(z)
    if form == 'arg':
        return math.atan2(x,y)
    if form == 'ang':
        return math.atan2(x,y)*180/3.1416

    # raw property (i.e., real, imag, conjugate)
    return getattr(x,form)

if __name__ == "__main__":

    raise NotImplementedError("cannot run framework as a script")
