"""GridLAB-D Subcommand Support Utilities"""

import sys

EXENAME = None
"""Executable name to use when output message are generated"""

E_OK = 0
"""Normal exit code"""

E_SYNTAX = 1
"""Syntax error exit code"""

E_ERROR = 2
"""General error exit code"""

E_EXCEPTION = 9
"""General exception exit code"""

VERBOSE = False
"""Enable verbose output"""

DEBUG = False
"""Enable traceback on exceptions"""

ERROR = True
"""Enable suppression of all unnecessary output"""

WARNING = True
"""Enable warning output"""

OUTPUT = {
        "standard": sys.stdout,
        "verbose": sys.stderr,
        "warning": sys.stderr,
        "error": sys.stderr,
        "exception": sys.stderr,
        }
"""Message output streams"""

class SubcommandSyntaxError(Exception):
    """Syntax error"""

def check_syntax(
    docs:str,
    *,
    args:list[str]|None=None,
    nargs:int=0):
    """Check for basic syntax of command line

    Arguments
    ---------

    - `docs`: Document string to use to locate syntax string
    - `args`: argument list to check (default is sys.argv[1:])
    - `nargs`: Minimum number of additional arguments required

    Exceptions
    ----------

    - `SubcommandSyntaxError`: raised when the syntax is not correct
    """
    if args is None:
        args = sys.argv[1:] if len(sys.argv) > 1 else []

    if len(args) < nargs:
        msg = [x for x in docs.split("\n") if x.startswith("Syntax: ")][0]
        raise SubcommandSyntaxError(msg)

def output(*args,**kwargs):
    if not "file" in kwargs: kwargs["file"] = OUTPUT["standard"]
    print(*args,**kwargs)

def verbose(*args,**kwargs):
    if VERBOSE:
        if not "file" in kwargs: kwargs["file"] = OUTPUT["verbose"]
        print(f"VERBOSE [{EXENAME}]:",*args,**kwargs)

def warning(*args,**kwargs):
    if WARNING:
        if not "file" in kwargs: kwargs["file"] = OUTPUT["warning"]
        print(f"WARNINGS [{EXENAME}]:",*args,**kwargs)
        
def error(*args,exitcode:int=None,**kwargs):
    if ERROR:
        if not "file" in kwargs: kwargs["file"] = OUTPUT["error"]
        print(f"ERROR [{EXENAME}]:",*args,**kwargs)
    if not exitcode is None:
        sys.exit(exitcode)
        
def exception(e_type,*args,**kwargs):
    if DEBUG and not e_type is None:
        if not "sep" in kwargs: kwargs["sep"] = " "
        raise e_type(kwargs["sep"].join(args))
    else:
        if not "file" in kwargs: kwargs["file"] = OUTPUT["exception"]
        if e_type is None:
            print(f"EXCEPTION [{EXENAME}]:",*args,**kwargs)
        else:
            print(f"EXCEPTION [{EXENAME}]: ({e_type.__name__})",*args,**kwargs)
        sys.exit(E_EXCEPTION)
        