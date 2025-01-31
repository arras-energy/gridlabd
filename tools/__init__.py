"""GridLAB-D python package

All the python modules installed in the GLD_ETC folder can be loaded
using the `gridlabd` package.
"""
# support legacy method of accessing core
try:
    from gldcore import *
except:
    pass