"""Make docs from python module

Syntax: python3 makemd.py NAME PATH

This tool convert the gridlabd python module NAME to a docs markdown file in the target
folder PATH.
"""

import os
import sys
import importlib
import inspect

EXEC = os.path.basename(sys.argv[0])

E_OK = 0
E_INVALID = 1
E_MISSING = 2
E_SYNTAX = 3
E_EXCEPTION = 9

IGNORE = ['TypeVar','Union']

class MakemdError(Exception):
    def __init__(self,msg,exitcode=None):
        self.exitcode = exitcode
        super().__init__(msg)

try:
    if len(sys.argv) == 1:
        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        sys.exit(E_SYNTAX)

    if len(sys.argv) == 2:
        raise MakemdError("missing path",E_MISSING)

    NAME = sys.argv[1]
    PATH = sys.argv[2]

    if "/usr/local/opt/current/gridlabd/share" not in sys.path:
        sys.path.append("/usr/local/opt/current/gridlabd/share")
    module = importlib.import_module("gridlabd." + NAME)

    with open(os.path.join(PATH,NAME.title()+".md"),"w") as md:

        # output header docs
        print(f"""[[/{os.path.join(PATH.replace("docs/",""),NAME.title())}]] -- {module.__doc__}
""",file=md)

        # output classes
        first = True
        for item in [getattr(module,x) for x in dir(module) if inspect.isclass(getattr(module,x))]:
            if not item.__doc__ or item.__name__ in IGNORE or isinstance(item,type(os)):
                continue
            if first:
                print("\n# Classes",file=md)
                first = False
            else:
                print("\n---",file=md)
            NL='\n'
            print(f"\n## {item.__name__}{NL*2}{NL.join([x.strip() for x in item.__doc__.split(NL)])}",file=md)

            for member in [getattr(item,x) for x in dir(item) if not x.startswith('_') or x == "__init__"]:
                if not member.__doc__ or not hasattr(member,"__annotations__"):
                    continue
                if member.__name__ == "__init__":
                    name = item.__name__
                    returns = ""
                else:
                    name = f"{item.__name__}.{member.__name__}"
                    returns = member.__annotations__['return'] if 'return' in member.__annotations__ else 'None'
                    returns = " -> " + (returns.__name__ if hasattr(returns,'__name__') else str(returns))
                args = [f"{x}:{t.__name__ if hasattr(t,'__name__') else str(t)}" for x,t in member.__annotations__.items() if x != "return"]
                docs = NL.join([x.strip() for x in member.__doc__.split(NL)])
                print(f"\n### `{name}({', '.join(args)}){returns}`{NL*2}{docs}",file=md)

        # output functions
        first = True
        for item in [getattr(module,x) for x in dir(module) if inspect.isfunction(getattr(module,x))]:
            if not item.__doc__ or item.__name__ in IGNORE:
                continue
            if first:
                print("\n# Functions",file=md)
                first = False
            else:
                print("\n---",file=md)
            NL='\n'
            args = [f"{x}:{t.__name__}" for x,t in item.__annotations__.items() if hasattr(t,__name__) and x != "return"]
            returns = item.__annotations__['return'].__name__ if 'return' in item.__annotations__ and hasattr(item.__annotations__['return'],'__name__') else 'None'
            docs = NL.join([x.strip() for x in item.__doc__.split(NL)])
            print(f"\n## `{item.__name__}({', '.join(args)}) -> {returns}`{NL*2}{docs}",file=md)


        # output constants
    
except MakemdError as err:

    print(f"ERROR [{EXEC}]: {err}",file=sys.stderr)
    if isinstance(err.exitcode,int):
        exit(err.exitcode)

except SystemExit:

    pass

except:

    e_type,e_value,e_trace = sys.exc_info()
    print(f"EXCEPTION [{EXEC}]: {e_type.__name__}({os.path.basename(e_trace.tb_frame.f_code.co_filename)}@{e_trace.tb_lineno}) {e_value}",file=sys.stderr)
    exit(E_EXCEPTION)
