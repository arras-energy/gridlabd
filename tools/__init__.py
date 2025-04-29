"""GridLAB-D python package

All the python modules installed in the GLD_ETC folder must be loaded
using the `gridlabd` package.
"""

# support legacy method of accessing core
# import os
# import sys
# import inspect
try:

    from gldcore import *

    # # find original gridlabd call by skipping past python internals
    # caller = inspect.getframeinfo(inspect.stack()[0][0])
    # # print(f"***TRACEBACK*** {os.path.basename(caller.filename)}@{caller.lineno}",file=sys.stderr)
    # n = 1
    # while not isinstance(caller.filename,str) or caller.filename.startswith("<") or caller.filename.endswith("__init__.py"):
    #     try:
    #         caller = inspect.getframeinfo(inspect.stack()[n][0])
    #         # print(f"***TRACEBACK*** {os.path.basename(caller.filename)}@{caller.lineno}",file=sys.stderr)
    #         n += 1
    #     except IndexError:
    #         break

    #     # ignore issue for subcommands
    # if not caller.filename.startswith(os.environ['GLD_ETC']): 
    #     warning(f"[{os.path.basename(caller.filename)}@{caller.lineno} from '{' '.join(sys.argv)}']: use of `import gridlabd` is deprecated and will result in an error soon. Use `import gldcore` instead.")

except ModuleNotFoundError: # ignore non-runtime module issues

    pass