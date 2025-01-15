"""Tool framework

The `framework` module contains the infrastructure to support standardized
implementation of tools in GridLAB-D.

Standard options:

The following options are processed by `read_stdargs()`:

* `--debug`: enable debug traceback on exception

* `--quiet`: suppress error messages

* `--silent`: suppress all error messages

* `--warning`: suppress warning messages

* `--verbose`: enable verbose output, if any

Example:

~~~
import framework as app

def main(argv):

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        # TODO: add options here

        else:
            error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # TODO: code implementation here, if any

    return app.E_OK

if __name__ == "__main__":

    try:

        # TODO: development testing -- delete when done writing code
        if not sys.argv[0]:
            sys.argv = ["selftest","--debug"]

        rc = main(sys.argv)
        exit(rc)

    except KeyboardInterrupt:

        exit(app.E_INTERRUPT)

    except Exception as exc:

        if DEBUG:
            raise exc

        if not QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[1]
            print(f"EXCEPTION [{app.EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(app.E_EXCEPTION)
~~~
"""
import os
import sys
import io
import json
import math
import subprocess
import unitcalc
from typing import TypeVar
import inspect
import traceback

EXEPATH = None
EXEFILE = None
EXENAME = None
EXETYPE = None

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

def read_stdargs(argv:list[str]) -> list[str]:
    """Read framework options

    Arguments:

    * `argv`: the argument list from which to read framework options

    Returns:

    * Remaining arguments
    """
    result = []
    global EXEPATH
    EXEPATH = argv[0]
    global EXEFILE
    EXEFILE = os.path.basename(EXEPATH)
    global EXENAME,EXETYPE
    EXENAME,EXETYPE = os.path.splitext(EXEFILE)
    for arg in list(argv[1:]):
        if arg in ["--debug"]:
            global DEBUG
            DEBUG = True
            argv.remove(arg)
        elif arg in ["--verbose"]:
            global VERBOSE
            VERBOSE = True
            argv.remove(arg)
        elif arg in ["--quiet"]:
            global QUIET
            QUIET = True
            argv.remove(arg)
        elif arg in ["--silent"]:
            global SILENT
            SILENT = True
            argv.remove(arg)
        elif arg in ["--warning"]:
            global WARNING
            WARNING = False
            argv.remove(arg)
        elif "=" in arg:
            key,value = arg.split("=",1)
            result.append((key,value.split(",")))
        else:
            result.append((arg,[]))
    debug("DEBUG =",DEBUG)
    debug("EXEFILE =",EXEFILE)
    debug("EXENAME =",EXENAME)
    debug("EXEPATH =",EXEPATH)
    debug("EXETYPE =",EXETYPE)
    debug("QUIET =",QUIET)
    debug("SILENT =",SILENT)
    debug("VERBOSE =",VERBOSE)
    debug("WARNING =",WARNING)
    debug("ARGV =",result)
    return result

def output(*msg:list,**kwargs):
    """General message output

    Arguments:

    * `msg`: message to output

    * `**kwargs`: print options

    Messages are suppressed when the `--silent` option is used.
    """
    if not "file" in kwargs:
        kwargs["file"] = sys.stdout
    if not SILENT:
        print(*msg,**kwargs)

def exception(exc:[TypeVar('Exception')|str]):
    """Exception message output

    Arguments:

    * `exc`: exception to raise
    """
    if isinstance(exc,str):
        exc = MapError(exc)
    raise exc

def error(*msg:list,code:[int|None]=None,**kwargs):
    """Error message output

    Arguments:

    * `msg`: message to output

    * `**kwargs`: print options

    Messages are suppressed when the `--quiet` option is used.
    """
    if not QUIET:
        if code:
            print(f"ERROR [{EXENAME}]: {' '.join([str(x) for x in msg])} (code {repr(code)})",file=sys.stderr,**kwargs)
        else:
            print(f"ERROR [{EXENAME}]: {' '.join([str(x) for x in msg])}",file=sys.stderr,**kwargs)
    if DEBUG:
        raise MappingError(msg)
    if not code is None:
        sys.exit(code)

def verbose(*msg:list,**kwargs):
    """Verbose message output

    Arguments:

    * `msg`: message to output

    * `**kwargs`: print options

    Messages are enabled when the `--verbose` option is used.
    """
    if VERBOSE:
        print(f"VERBOSE [{EXENAME}]: {' '.join([str(x) for x in msg])}",file=sys.stderr,**kwargs)

def warning(*msg:list,**kwargs):
    """Warning message output

    Arguments:

    * `msg`: message to output

    * `**kwargs`: print options

    Messages are suppress when the `--warning` option is used.
    """
    if WARNING:
        print(f"WARNING [{EXENAME}]: {' '.join([str(x) for x in msg])}",file=sys.stderr,**kwargs)

def debug(*msg:list,**kwargs):
    """Debugging message output

    Arguments:

    * `msg`: message to output

    * `**kwargs`: print options

    Messages are enabled when the `--debug` option is used.
    """
    if DEBUG:
        print(f"DEBUG [{EXENAME}]: {' '.join([str(x) for x in msg])}",file=sys.stderr,**kwargs)

def gridlabd(*args:list[str], bin=True, **kwargs) -> TypeVar('subprocess.CompletedProcess')|None:
    """Simple gridlabd runner

    Arguments:

    * `args`: argument list

    * `bin`: enable direct call to gridlabd binary (bypasses shell and faster)

    * `kwargs`: options to pass to `subpocess.run`

    Returns:

    * Complete process object (see `subprocess.CompleteProcess`)

    See also:

    * https://docs.python.org/3/library/subprocess.html
    """
    if not "capture_output" in kwargs:
        kwargs["capture_output"] = True
    result = None
    try:
        cmd = ["gridlabd.bin" if bin and "GLD_BIN" in os.environ else "gridlabd"] + list(args)
        debug(f"Running {cmd} with options {kwargs}")
        result = subprocess.run(cmd,**kwargs)
        return result
    except:
        return None

def open_glm(file:str,
        tmp:str=None,
        init:bool=False,
        exception=True,
        passthru=True,
        ) -> TypeVar('io.TextIOWrapper'):
    """Open GLM file as JSON

    Arguments:

    * `file`: GLM filename

    * `tmp`: temporary folder to store JSON file

    * `init`: enable model initialization during conversion

    * `exception`: enable raising exception instead of returning (None,result)

    * `passthru`: enable passing stderr output through to app

    Return:

    * File handle to JSON file after conversion from GLM
    """
    if tmp is None:
        tmp = "."
    outfile = os.path.join(tmp,os.path.splitext(os.path.basename(file))[0]+".json")
    result = gridlabd("-I" if init else "-C",file,"-o",outfile)
    if passthru:
        for msg in result.stderr.decode("utf-8").split("\n"):
            if WARNING and msg.startswith("WARNING "):
                output(msg,file=sys.stderr)
            elif not QUIET and msg.startswith("ERROR ") or msg.startswith("FATAL "):
                output(msg,file=sys.stderr)
            elif VERBOSE and msg.startswith("VERBOSE "):
                output(msg,file=sys.stderr)
    if result.returncode != 0:
        if exception:
            raise RuntimeError("GLM conversion to JSON failed")
        return None,result
    return open(outfile,"r"),result

def version(terms:str=None) -> str:
    """Get gridlabd version

    Returns:

    * GridLAB-D version info
    """
    _version = gridlabd(f"--version={terms}" if terms else "--version")
    return _version.stdout.decode('utf-8').strip() if _version and _version.returncode==0 else ""

def double_unit(x:str) -> float:
    """Convert a string with unit to a float

    * `x`: string representing real value

    Returns:

    * real value
    """
    return float(x.split(" ",1)[0])

def integer(x:str) -> int:
    """Convert a string to an integer

    * `x`: string representing integer value

    Returns:

    * integer value
    """
    return int(x)

def complex_unit(x:str,
        form:str=None,
        prec:str=2,
        unit:str=None) -> [str|float|tuple[float]|complex]:
    """Convert complex value with unit

    Arguments:

    * `form`: formatting (default is None). Valid values are
      ('i','j','d','r','rect','mag','arg','ang','conjugate','real','imag','unit','str')

    * `prec`: precision (default is 2)

    * `unit`: unit to convert to (default is None)

    Returns:

    * `float`: value (if form is 'mag','arg','ang','real','imag')

    * `str`: formatted string (if form is 'i','j','d','r','unit','str')

    * `tuple[float]`: tuple (if form is 'rect')
    
    * `complex`: complex value (if form is 'conjugate' or None)
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
