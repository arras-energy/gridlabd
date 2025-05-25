"""Precompile python modules to check packages and speed up first-time imports

Syntax: gridlabd python precompile.py [PATTERN ...]


"""
import os
import sys
import re
import importlib

PATTERN = ".*"

def _findmatch(patterns,text):
    for x in patterns:
        if re.match(x,text):
            return x
    return None


sys.path = [x for x in sys.path if x.startswith("/usr/local")]

if __name__ == "__main__":
    patterns = sys.argv[1:] if len(sys.argv) > 1 else [PATTERN]
    errors = 0
    for module in sorted(os.listdir(os.environ["PYTHON_LIB"])):
        if _findmatch(patterns,module) and os.path.exists(os.path.join(os.environ["PYTHON_LIB"],module,"__init__.py")):
            print("Compiling",module,end="...",flush=True)
            try:
                importlib.import_module(module)
                print("ok")
            except:
                e_type,e_name,e_trace = sys.exc_info()
                errors += 1
                print("ERROR",file=sys.stdout,flush=True)
                print(module+":",e_type.__name__,e_name,file=sys.stderr,flush=True)
    sys.exit(errors)
