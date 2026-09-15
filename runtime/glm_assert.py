"""GridLAB-D assert module

The `assert` runtime class is loaded using the following syntax.

    #include "assert.glm"

The `assert` object requires the parent object to be defined. The `assert`
object checks the target value of the parent at each time synchronization
`commit` event and stops the simulation if the assertion fails. An `assert`
object includes the following parameters.

Properties
----------

- `target`: Specifies the target property (and optionally the `part`, e.g.,
  `property.part`) of the parent object to monitor. The `part` value may be
  a callable member of the target object but cannot include any parameters.

- `relation`: Specifies the comparison to use when checking the `value`
  asserted.
    - `EQ`: `target` must be strictly equal to `value`.
    - `LT`: `target` must be strictly less than `value`.
    - `LE`: `target` must be less than or equal to `value`.
    - `GT`: `target` must be strictly greater than `value`.
    - `GE`: `target` must be greater than or equal to `value`.
    - `NE`: `target` must be strictly not equal to `value`.
    - `IN`: `target` must be strictly between `lower` and `upper`.
    - `NI`: `target` must not be strictly between `lower` and `upper`.

- `value`: Specifies the value to which the `target` is compared.

- `dtype`: Overrides the default data type to use for comparing `target` and
  `value`. The default is automatically determine the data type based on the
  `target` property data type.

- `within`: Relaxes the `relation` to include a tolerance for all strict
  comparisons.

- `lower`: Specifies the `lower` bound for `IN` and `NI` comparisons.

- `upper`: Specifies the `upper` bound for `IN` and `NI` comparisons.

- `start`: Specifies at what simulation time to start checking the `target`.

- `stop`: Specifies at what simulation time to stop checking the `target`.

- `status`: Indicates the status of the last check.
    - `INIT`: The assertion has yet to be performed.
    - `TRUE`: The last assertion passed.
    - `FALSE`: The last assertion failed.
    - `ERROR`: The last assertion resulted in an exception.
    - `WAITING`: The assertion is waiting for the `start` time.
    - `STOPPED`: The assertion has passed the `stop` time.

- `on_failure`: Specifies the handling of failed assertions.
    - `ERROR`: Failure causes the simulation to halt (default).
    - `WARNING`: Failure causes a warning message only.
    - `EXCEPTION`: Failure raises an exception.
    - `IGNORE`: Failures are ignored.

Example
-------

The following example creates a test object and assert the equality of the
target value.

    #include "assert.glm"

    class test
    {
        double x;
    }

    object test
    {
        x 1.23;
        object assert
        {
            target x;
            relation EQ;
            value 1.23;
            within 0.01;
        };
    }
"""

import sys
import re
from math import fabs, sin, cos, pi, atan2, sqrt
from datetime import datetime

from glm_utilities import MutableData, value_unit, autotype
import glm_timestamp

_checklist = {}

def _void(_):
    return None

def _double(s):
    try:
        return float(s)
    except:
        raise ValueError(f"{repr(s)} is not a valid GridLAB-D double value")

class _Complex(complex):
    """Complex object that supports additional parts besides `real` and `imag`"""
    def __new__(cls,x,y=0):
        return super().__new__(cls,x,y)

    def abs(self):
        """Magnitude"""
        return sqrt(self.real**2 + self.imag**2)

    def mag(self):
        """Magnitude"""
        return sqrt(self.real**2 + self.imag**2)
        
    def arg(self):
        """Angle in radians"""
        return atan2(self.real,self.imag)

    def ang(self):
        """Angles in degrees"""
        return self.arg() * 180 / pi

def _complex(s):
    if isinstance(s,complex):
        return _Complex(s.real,s.imag)
    try:
        return _Complex(float(s))
    except:
        pass
    try:
        (x,y,notation) = re.match(r"(^[+-]?(?:\d+|\d*\.\d+)(?:[eE][+-]?\d+)?)([+-](?:\d+|\d*\.\d+)(?:[eE][+-]?\d+)?)([ijrd])$",s).groups()
        x = float(x)
        y = float(y)
        match notation:
            case 'i':
                return _Complex(x,y)
            case 'j':
                return _Complex(x,y)
            case 'r':
                return _Complex(x*cos(y),x*sin(y))
            case 'd':
                y *= pi/1800
                return _Complex(x*cos(y),x*sin(y))
            case '_':
                raise "invalid notation"
    except Exception as err:
        raise ValueError(f"{repr(s)} is not a valid GridLAB-D complex value") from err

def _int16(s):
    return int(s)

def _int32(s):
    return int(s)

def _int64(s):
    return int(s)

def _bool(s):
    if isinstance(s,bool):
        return s
    if isinstance(s,int):
        return s!=0
    assert s in ["TRUE","FALSE"], f"{repr(s)} is not a valid GridLAB-D boolean value"
    return s == "TRUE"

def _timestamp(s):
    if isinstance(s,(int,float)):
        return int(s)
    if s == "":
        return gldcore.INVALID
    elif s == "NEVER":
        return gldcore.NEVER
    elif s == "INIT":
        return gldcore.get_global("starttime")
    return int(datetime.fromisoformat(s).timestamp())

def _python(s):
    return eval(s)

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
    if "." in target:
        target,_part = target.split(".",1)
    else:
        _part = None
    if ":" in target:
        prop = target.split(":",1)
    elif parent is None:
        raise ValueError(f"{obj}.{target=} missing parent/target object")
    else:
        prop = (parent,target)
    relation = gldcore.get_value(obj,"relation")
    dtype = gldcore.get_value(obj,"dtype")
    if not dtype:
        pclass = gldcore.get_object(prop[0])["class"]
        dtype = gldcore.get_class(pclass)[prop[1]]["type"]
    try:
        dtype = globals()[f"_{dtype}"]
    except KeyError:
        dtype = str

    glm_timestamp.TIMEZONE_LOCALE = gldcore.get_global("timezone_locale")
    try:
        start = glm_timestamp.TIMESTAMP(gldcore.get_value(obj,"start"))
    except ValueError:
        start = 0
    try:
        stop = glm_timestamp.TIMESTAMP(gldcore.get_value(obj,"stop"))
    except ValueError:
        stop = gldcore.NEVER

    value = gldcore.get_value(obj,"value")
    if dtype == _complex:
        value = float(value)
        ttype = float
    elif value == "":
        value = None
        ttype = dtype
    else:
        value = dtype(value)
        ttype = dtype

    within = float(gldcore.get_value(obj,"within"))

    lower = gldcore.get_value(obj,"lower")
    lower = ttype(lower) if lower != "" else None

    upper = gldcore.get_value(obj,"upper")
    upper = ttype(upper) if upper != "" else None

    if _part:    
        def part(x):
            y = getattr(x,_part)
            return y() if callable(y) else y
    else:
        def part(x):
            return x

    match relation:
        case "EQ":
            if within:
                test = lambda x: fabs(x-value) < within
            else:
                test = lambda x: x == value
        case "NE":
            if within:
                test = lambda x: fabs(x-value) >= within
            else:
                test = lambda x: x != value
        case "LT": 
            test = lambda x: x < value
        case "LE":
            test = lambda x: x <= value
        case "GT":
            test = lambda x: x > value
        case "GE":
            test = lambda x: x >= value
        case "IN":
            assert not lower is None, f"{obj}.{lower=} is not specified"
            assert not upper is None, f"{obj}.{upper=} is not specified"
            test = lambda x: lower < x < upper
        case "NI":
            assert not lower is None, f"{obj}.{lower=} is not specified"
            assert not upper is None, f"{obj}.{upper=} is not specified"
            test = lambda x: not ( lower < x < upper )
        case _:
            raise ValueError(f"{obj}.{relation=} is not valid")

    if not obj in _checklist:
        _checklist[obj] = []
    _checklist[obj].append(MutableData(
        test=test,
        start=glm_timestamp.TIMESTAMP(start),
        stop=gldcore.NEVER if stop == 0 else glm_timestamp.TIMESTAMP(stop),
        prop=gldcore.property(*prop),
        dtype=dtype,
        ttype=ttype,
        value=value,
        relation=relation,
        part=part,
        lower=lower,
        upper=upper,
        status="INIT",
        on_failure=gldcore.get_value(obj,"on_failure"),
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
    for check in _checklist[obj]:
        try:
            result = check.part(check.dtype(check.prop.get_value()))
            if t < check.start:
                check.status = "WAITING"
                gldcore.verbose(f"{check.prop=} assert {obj=} not started ({check.start=})")
            elif t > check.stop:
                check.status = "STOPPED"
                gldcore.verbose(f"{check.prop=} assert {obj=} stopped ({check.stop=})")
            elif not check.test(result):
                check.status = "FALSE"
                match check.on_failure:
                    case "ERROR":
                        gldcore.error(f"{obj=} {check=} {result=} failed at {t=}")
                    case "EXCEPTION":
                        raise Exception(f"{obj=} {check=} {result=} failed at {t=}")
                    case "WARNING":
                        gldcore.warning(f"{obj=} {check=} {result=} failed at {t=}")
                    case "IGNORE":
                        pass
                    case _:
                        raise ValueError(f"{check.on_failure=} is not valid")
            else:
                check.status = "TRUE"
                gldcore.verbose(f"{obj=} {check=} {result=} passed at {t=}")
        except:
            e_type,e_value,_ = sys.exc_info()
            gldcore.error(f"{obj=} exception {e_type.__name__}({e_value}) caught")
            check.status = "ERROR"
        gldcore.set_value(obj,"status",check.status)

    return gldcore.NEVER

