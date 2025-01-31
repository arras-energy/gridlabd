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
import gridlabd.framework as app

def main(argv:list[str]) -> int:

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        # add your options here

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement your code here

    # normal termination condigion
    return app.E_OK

if __name__ == "__main__":

    app.run(main)
~~~
"""
import os
import sys
import io
import json
import math
import subprocess
import gridlabd.unitcalc as unitcalc
import geocoder
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
E_NOTFOUND = 5 # value not found
E_FAILED = 6 # operation failed
E_INTERRUPT = 8 # interrupted
E_EXCEPTION = 9 # exception raised

class ApplicationError(Exception):
    """Application exception"""

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

    If `exc` is a string, an `ApplicationError` exception is raised.
    """
    if isinstance(exc,str):
        exc = ApplicationError(exc)
    raise exc

def error(*msg:list,code:[int|None]=None,**kwargs):
    """Error message output

    Arguments:

    * `msg`: message to output

    * `**kwargs`: print options

    Messages are suppressed when the `--quiet` option is used.

    If `--debug` is enabled, an exception is raised with a traceback.

    If the exit `code` is specified, exit is called with the code.
    """
    if not QUIET:
        if code:
            print(f"ERROR [{EXENAME}]: {' '.join([str(x) for x in msg])} (code {repr(code)})",file=sys.stderr,**kwargs)
        else:
            print(f"ERROR [{EXENAME}]: {' '.join([str(x) for x in msg])}",file=sys.stderr,**kwargs)
    if DEBUG:
        raise ApplicationError(*msg)
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

def gridlabd(*args:list[str], 
    bin=True, 
    output_to=None,
    **kwargs,
    ) -> TypeVar('subprocess.CompletedProcess')|None:
    """Simple gridlabd runner

    Arguments:

    * `args`: argument list

    * `bin`: enable direct call to gridlabd binary (bypasses shell and faster)

    * `output_to`: run postprocessor on output to stdout

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
        return output_to(result.stdout.decode("utf-8")) if output_to else result
    except:
        return None

LOCATION = None
def location(refresh=False):
    global LOCATION
    if refresh or LOCATION is None:
        LOCATION = geocoder.ip('me').geojson['features'][0]['properties']
    return LOCATION

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
            raise ApplicationError("GLM conversion to JSON failed")
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

def syntax(docs:str,print=print):
    """Print syntax message

    Arguments:

    * `docs`: the application's __doc__ string

    * `print`: the print function to use (default is `print`)

    This function does not return. When the function is done it calls exit(E_SYNTAX)
    """
    print("\n".join([x for x in docs.split("\n") if x.startswith("Syntax: ")]))
    exit(E_SYNTAX)

def run(main:callable,exit=exit,print=print):
    """Run a main function under this app framework

    Arguments:

    * `main`: the main function to run

    * `exit`: the exit function to call (default is `exit`)

    * `print`: the print funtion to call on exceptions (default is `print`)

    This function does not return. When the app is done it calls exit.
    """
    try:

        rc = main(sys.argv)
        exit(rc)

    except KeyboardInterrupt:

        exit(app.E_INTERRUPT)

    except Exception as exc:

        if DEBUG:
            raise exc

        if not QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[-1]
            print(f"EXCEPTION [{EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(E_EXCEPTION)


if __name__ == "__main__":

    raise ApplicationError("cannot run framework as a script")
