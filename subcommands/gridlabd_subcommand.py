"""GridLAB-D Subcommand Support Utilities"""

import sys

E_OK = 0
E_SYNTAX = 1
E_ERROR = 2
E_EXCEPTION = 9

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
