"""GridLAB-D assert module

TODO
"""

import sys
from math import fabs
from datetime import datetime

from glm_utilities import MutableData, value_unit, autotype
import glm_timestamp

checklist = {}

def assert_init(obj,t):
    """Assert commit event handler

        Arguments
    ---------
    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------
    - `int`: next timestamp
    """
    parent = gldcore.get_value(obj,"parent")
    target = gldcore.get_value(obj,"target")
    if ":" in target:
        prop = target.split(":",1)
    elif parent is None:
        raise ValueError(f"{obj}.{target=} missing parent/target object")
    else:
        prop = (parent,target)
    relation = gldcore.get_value(obj,"relation")
    dtype = gldcore.get_value(obj,"dtype")
    if not dtype:
        dtype = str
    elif dtype in ["int","float","complex","datetime","str"]:
        dtype = eval(dtype)
    else:
        raise ValueError(f"{dtype=} is invalid")
    value = dtype(gldcore.get_value(obj,"value"))
    within = float(gldcore.get_value(obj,"within"))
    lower = float(gldcore.get_value(obj,"lower"))
    upper = float(gldcore.get_value(obj,"upper"))
    glm_timestamp.TIMEZONE_LOCALE = gldcore.get_global("timezone_locale")
    try:
        start = glm_timestamp.TIMESTAMP(gldcore.get_value(obj,"start"))
    except ValueError:
        start = 0
    try:
        stop = glm_timestamp.TIMESTAMP(gldcore.get_value(obj,"stop"))
    except ValueError:
        stop = gldcore.NEVER
    match relation:
        case "EQ":
            if within:
                test = lambda x: fabs(float(x)-value) < within
            else:
                test = lambda x: x == value
        case "NE":
            if within:
                test = lambda x: fabs(float(x)-value) >= within
            else:
                test = lambda x: dtype(x) != value
        case "LT": 
            test = lambda x: dtype(x) < value
        case "LE":
            test = lambda x: dtype(x) <= value
        case "GT":
            test = lambda x: dtype(x) > value
        case "GE":
            test = lambda x: dtype(x) >= value
        case "IN":
            assert not lower is None, f"{obj}.{lower=} is not specified"
            assert not upper is None, f"{obj}.{upper=} is not specified"
            test = lambda x: lower < dtype(x) < upper
        case "NI":
            assert not lower is None, f"{obj}.{lower=} is not specified"
            assert not upper is None, f"{obj}.{upper=} is not specified"
            test = lambda x: not ( lower < dtype(x) < upper )
        case _:
            raise ValueError(f"{obj}.{relation=} is not valid")

    if not obj in checklist:
        checklist[obj] = []
    checklist[obj].append(MutableData(
        test=test,
        start=glm_timestamp.TIMESTAMP(start),
        stop=gldcore.NEVER if stop == 0 else glm_timestamp.TIMESTAMP(stop),
        prop=gldcore.property(*prop),
        dtype=dtype,
        value=value,
        relation=relation,
        ))

    return gldcore.INIT_OK

def assert_commit(obj,t):
    """Assert commit event handler

        Arguments
    ---------
    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------
    - `int`: next timestamp
    """
    for check in checklist[obj]:
        value = check.prop.get_value()
        if t < check.start:
            gldcore.verbose(f"{check.prop=} assert {obj=} not started ({check.start=})")
            gldcore.set_value(obj,"status","WAITING")
        elif t > check.stop:
            gldcore.verbose(f"{check.prop=} assert {obj=} stopped ({check.stop=})")
            gldcore.set_value(obj,"status","STOPPED")
        elif not check.test(value):
            gldcore.error(f"{check.prop=} {value=} assert {obj=} failed at {t=}")
            gldcore.set_value(obj,"status","FALSE")
        else:
            gldcore.verbose(f"{check.prop=} {value=} assert {obj} passed {check.test} at {t=}")
            gldcore.set_value(obj,"status","TRUE")

    return gldcore.NEVER
