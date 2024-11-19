"""Unit support

Syntax: gridlabd unitcalc VALUE [VALUE OP [...]] [OPTIONS ...]

Options:

* `--unit=[UNIT[,...]]`: units to convert stack when output results

* `help`: display this help

* `list`: list of primitives in unit dictionary

* `test`: perform self-test

The `unitcalc` tool support unit arithmetic and unit conversion for shell
scripts and Python applications. All arguments are in RPN, e.g., "2 3 +". 

The number of comma-delimited units, if specified, must match the number of
results in the stack.

Values may be provided with or without units. Values without units are
considered compatible with values that have using, i.e., the same unit for
summation and scalars for products.  Units must always be provided with a
space separating the number from the unit.

It is important to know that composite units are calculated as needed from
primitive units, e.g., although `m/s` is not listed, it is supported.

Supported operators include the following:

* `+`, `add`, `sum`: addition

* `-`, `sub`, `subtract`,`minus`: subtraction

* `*`, `x`, `mul`, `multiply`, `prod`, `product`: multiplication

* `/`, `div`, `divide``: division

* `//`, `quo`, `quotient`, `floordiv`, `fdiv`: floor division (quotient)

* `%`, `mod`, `modulo`, `rem`, `remainder`: modulo (remainder)

* `^`, `**`, `pow`, `power`: power

The following stack operations are also supported:

* `copy`: copy the head item

* `pop`:

* `rol`: rotate stack left

* `ror`: rotate stack right

* `rev`: reverse stack

* `swap`, `exchange`: swap the top two stack items

Examples:

    $ gridlabd unitcalc "32 degF" --unit=degC
    0 degC

    $ gridlabd unitcalc "32.2 ft/s^2" "5 lb" x --unit=N
    22.2591 N

"""

import sys
import os
import copy
import re
import math
from typing import TypeVar

# c - speed on light
# e - electric charge
# h - Plank's constant
# k - Boltzmann's constant
# m - electron mass
# s - currency unit
TAGS = ["c","e","h","k","m","s","scale","offset","prec"]
UNITS = {
    "unit" : [0,0,0,0,0,0,1,0,15],
    "m" : [-1,0,1,0,-1,0,4.121487e01,0,7],
    "g" : [0,0,0,0,1,0,1.09775094e27,0,10],
    "s" : [-2,0,1,0,-1,0,1.235591e10,0,7],
    "A" : [2,1,-1,0,1,0,5.051397e08,0,7],
    "K" : [2,0,0,-1,1,0,1.686358e00,0,7],
    "cd" : [4,0,-1,0,2,0,1.447328E+00,0,7],
    "$" : [0,0,0,0,1,1,1.097751e30,0,7],
}
SCALARS = {
    "Y" : 24,
    "Z" : 21,
    "E" : 18,
    "P" : 15,
    "T" : 12,
    "G" : 9,
    "M" : 6,
    "k" : 3,
    "h" : 2,
    "da" : 1,
    "d" : -1,
    "c" : -2,
    "m" : -3,
    "u" : -6,
    "n" : -9,
    "p" : -12,
    "f" : -15,
    "a" : -18,
    "z" : -21,
    "y" : -24,
}
SPECS = {
    "pi" : "3.1415926536 unit",
    "rad" : "0.159155 unit",
    "deg" : "0.0027777778 unit",
    "grad" : "0.0025 unit",
    "quad" : "0.25 unit",
    "sr" : "0.5 rad",

    #  Derived SI
    "R" : "0.55555556 K",
    "degC" : "K-273.14",
    "degF" : "R-459.65",
    "N" : "1 m*kg/s^2",
    "Pa" : "1 N/m^2",
    "J" : "1 N*m",

    #  Time
    "min" : "60 s",
    "h" : "60 min",
    "day" : "24 h",
    "wk" : "7 day",
    "yr" : "365 day",
    "syr" : "365.24 day",

    #  Length
    "in" : "0.0254 m",
    "ft" : "12 in",
    "yd" : "3 ft",
    "mile" : "5280 ft",

    #  Area
    "sf" : "1 ft^2",
    "sy" : "1 yd^2",
    "ha" : "10000 m^2",

    #  Volume
    "cf" : "1 ft^3",
    "cy" : "1 yd^3",
    "gal" : "0.0037854118 m^3",
    "l" : "0.001 m^3",

    #  Mass
    "lb" : "0.453592909436 kg",
    "tonne" : "1000 kg",

    #  Velocity
    "mph" : "1 mile/h",
    "fps" : "1 ft/s",
    "fpm" : "1 ft/min",
    "mps" : "1 m/s",
    "knot" : "1.151 mph",

    #  Flow rates
    "gps" : "1 gal/s",
    "gpm" : "1 gal/min",
    "gph" : "1 gal/h",
    "cfm" : "1 ft^3/min",
    "ach" : "1 unit/h",

    #  Frequency
    "Hz" : "1 unit/s",

    #  EM units
    "W" : "1 J/s",
    "Wh" : "1 W*h",
    "Btu" : "0.293 W*h",
    "ton" : "12000 Btu/h", #  ton cooling
    "tons" : "1 ton*s", #  ton.second cooling
    "tonh" : "1 ton*h", #  ton.hour cooling
    "hp" : "746 W", #  horsepower
    "V" : "1 W/A", #  Volt
    "C" : "1 A*s", #  Coulomb
    "F" : "1 C/V", #  Farad
    "Ohm" : "1 V/A", #  resistance
    "H" : "1 Ohm*s", #  Henry
    "VA" : "1 V*A", #  Volt-Amp
    "VAr" : "1 V*A", #  Volt-Amp reactive
    "VAh" : "1 VA*h",
    "Wb" : "1 J/A", #  Weber
    "lm" : "1 cd*sr", #  lumen
    "lx" : "1 lm/m^2", #  lux
    "Bq" : "1 unit/s", #  Becquerel
    "Gy" : "1 J/kg", #  Grey
    "Sv" : "1 J/kg", #  Sievert
    "S" : "1 unit/Ohm", #  Siemens

    #  data
    "b" : "1 unit", #  1 bit
    "B" : "8 b", #  1 byte

    #  pressure
    "bar" : "100000 Pa",
    "psi" : "6894.757293178 Pa",
    "atm" : "98066.5 Pa",
    "inHg" : "3376.85 Pa", #  at 60degF
    "inH2O" : "248.843 Pa", #  at 60degF

    # other energy
    "EER" : "1 Btu/Wh",
    "ccf" : "1000 Btu",  #  this conflict with centi-cubic-feet (ccf)
    "therm" : "100000 Btu",
}

def _get_unit(unit):
    try:
        scale = float(unit)
        u = UNITS["unit"]
        return u[:6] + [scale] +u[7:]
    except:
        pass

    if not unit in UNITS:
        for prefix, scale in SCALARS.items():
            if unit.startswith(prefix) and unit[len(prefix):] in UNITS:
                UNITS[unit] = UNITS[unit[len(prefix):]].copy()
                UNITS[unit][6] *= 10**scale
                break
    return UNITS[unit]

def _derive(spec):
    if spec in UNITS:
        return UNITS[spec]
    try:
        scale = float(spec)
        offset = 0
        defn = "unit"
        prec = 16
    except Exception as err:
        spec = spec.strip()
        if " " in spec:
            scale, defn = spec.strip().split(" ")
            offset = 0
            scale = float(scale)
            prec = None # TODO: use the precision of the underlying units, positive precision is relative
        elif "-" in spec:
            defn, offset = spec.strip().split("-")
            scale = 1.0
            offset = -float(offset)
            prec = -2 # negative precision is absolute
        elif "+" in spec:
            defn, offset = spec.strip().split("+")
            scale = 1.0
            offset = float(offset)
            prec = -2 # negative precision is absolute
        else:
            scale = 1.0
            offset = 0.0
            defn = spec.strip()
            prec = None
    if "/" in defn:
        num,den = defn.split("/",1)
        if not num:
            num = "unit"
        if not den:
            den = "unit"
    else:
        num = defn
        den = "unit"
    args = UNITS["unit"][:6]
    if prec == None:
        prec = UNITS["unit"][8]
    if offset == 0.0:
        for item in num.split("*"):
            if "^" in item:
                item,expn = item.split("^",1)
            else:
                expn = 1
            try:
                u = _get_unit(item)
            except KeyError as err:
                u = None
            if u is None:
                raise ValueError(f"unit '{spec}' is not a valid numerator")
            for n,m in enumerate(u[:6]):
                args[n] += m*int(expn)
            scale *= u[6]**int(expn)
            prec = min(prec,u[8])
        for item in den.split("*"):
            if "^" in item:
                item,expn = item.split("^",1)
            else:
                expn = 1
            try:
                u = _get_unit(item)
            except KeyError as err:
                u = None
            if u is None:
                raise ValueError(f"unit '{spec}' is not valid a valid denominator")
            for n,m in enumerate(u[:6]):
                args[n] -= m*int(expn)
            scale /= u[6]**int(expn)
            prec = min(prec,u[8])
    else:
        unit = _get_unit(defn)
        args,scale = unit[:6],unit[6]
    args.extend([scale,offset,prec])
    return args

for unit,spec in SPECS.items():
    UNITS[unit] = _derive(spec)

class UnitException(Exception):
    pass

def _extend(a,b):
    def _expand(x):
        y = x.split('^')
        return [y[0],1] if len(y) == 1 else [y[0],int(y[1])]
    # print(a,b)
    aa = dict([_expand(x) for x in a])
    bb = dict([_expand(x) for x in b])
    for y,n in bb.items():
        if y in aa:
            aa[y] += bb[y]
        else:
            aa[y] = bb[y]
    # print(' -->',a,b)

def _split(unit,mul=1):
    result = {}
    if "/" in unit:
        num,den = unit.split("/")
        result = _split(num)
        for x,n in _split(den,-1).items():
            result[x] = (result[x]+n) if x in result else n
    else:
        for u in unit.split("*"):
            if '^' in u:
                x,n = u.split('^',1)
                n = int(n)
            else:
                x,n = u,1
            n *= mul
            result[x] = (result[x]+n) if x in result else n
    return {x:n for x,n in result.items() if n != 0}

def _join(terms,mul=1):
    num = []
    for x,n in terms.items():
        if n*mul > 0:
            num.append(f"{x}^{n*mul}" if n*mul > 1 else x)
    den = []
    for x,n in terms.items():
        if n*mul < 0:
            den.append(f"{x}^{-n*mul}" if n*mul < -1 else x)
    return "*".join(num) + ( f"/{'*'.join(den)}" if den else "" )

def _add(a,b):
    result = {x:n for x,n in a.items() if n != 0}
    for x,n in b.items():
        result[x] = (result[x]+n) if x in result else n
    return {x:n for x,n in result.items() if n != 0}

def _sub(a,b):
    result = {x:n for x,n in a.items() if n != 0}
    for x,n in b.items():
        result[x] = (result[x]-n) if x in result else -n
    return {x:n for x,n in result.items() if n != 0}


class Unit:
    """Unit handling class"""
    def __init__(self,unit):
        """Unit class constructor

        Arguments:

        * `unit (str)`: unit specification

        Unit objects support arithmetic for units, e.g., addition, subtraction,
        multiplication, division, powers, module, and boolean (non-)equality.
        """
        spec = _derive(unit)
        self.args = spec[:6]
        self.scale = spec[6]
        self.offset = spec[7]
        self.prec = spec[8]
        self.terms = _split(unit)
        self.unit = _join(self.terms)
        if not self.unit in UNITS:
            # print(self.unit,':',spec)
            UNITS[self.unit] = self.args + [self.scale,self.offset,self.prec]

    def __repr__(self):
        return f"<Unit:'{self.unit}',({self.args},{self.scale},{self.offset},{self.prec}),{self.terms})"

    def __str__(self):
        return _join(self.terms)

    def __mul__(self,other):
        if isinstance(other,Unit):
            return Unit(_join(_add(self.terms,other.terms)))
        return Unit(f"{other} {_join(self.terms)}")

    def __truediv__(self,other):
        if isinstance(other,Unit):
            return Unit(_join(_sub(self.terms,other.terms)))
        return Unit(_join(_sub(self.terms,Unit(str(other)).terms)))

    def __rmul__(self,other):
        if isinstance(other,Unit):
            return Unit(_join(_add(self.terms,other.terms)))
        return Unit(_join(_add(self.terms,Unit(str(other)).terms)))

    def __rtruediv__(self,other):
        if isinstance(other,Unit):
            return Unit(_join(_sub(self.terms,other.terms)))
        return Unit(_join(_sub(Unit(str(other)).terms,self.terms)))

    def __pow__(self,n):
        return Unit(_join(self.terms,n))

    def __eq__(self,other):
        if type(other) is str:
            other = Unit(other)
        return self.args == other.args and self.scale == other.scale

    def __ne__(self,other):
        if type(other) is str:
            other = Unit(other)
        return self.args != other.args or self.scale != other.scale

    def _invert(self):
        return Unit(_join(self.terms,-1))

    def matches(self,x:str|TypeVar('Unit'),exception=False,strict=False):
        """Verifies that two units are compatible for add/subtract operations

        Arguments:

        * `x (str|Unit)`: unit to check against

        * `exception (bool)`: raise exception on mismatch

        * `strict (bool)`: match with `None` units fails

        Returns:

        * `bool`: `True` if matched, otherwise `False`
        """
        if isinstance(x,str):
            x = Unit(x)
        elif isinstance(x,floatUnit):
            x = x.unit
        if x is None:
            return not strict
        if self.args == x.args:
            return True
        if not exception:
            return False
        raise UnitException("units do not match")

class floatUnit:
    """Float with unit class

    The `floatUnit` class supports all floating point arithmetic.
    """

    def __init__(self,value:float|int|str,unit:str|None=None):
        """Float with unit constructor

        Arguments:

        * `value (float|int|str)`: the floating point value (may include unit if `str`)

        * `unit`: unit (if not included in `value`)
        """
        self.unit = unit
        if type(value) is str and " " in value.strip():
            if isinstance(unit,str):
                raise UnitException("cannot use units in both value and unit")
            value,unit = value.strip().split(" ",1)
            self.unit = Unit(unit)
        elif isinstance(unit,str):
            self.unit = Unit(unit)
        elif unit is not None and not isinstance(unit,Unit):
            raise UnitException(f"{unit} is not a valid unit")
        self.value = float(value)

    def __str__(self):
        if self.unit:
            return f"{self.value:g} {self.unit}"
        else:
            return f"{self.value:g}"

    def __add__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value+x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value+x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value+x.value,x.unit)
        self.unit.matches(x.unit,True)
        return floatUnit(self.value+x.value/self.unit.scale*x.unit.scale,self.unit)

    def __sub__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value-x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value-x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value-x.value,x.unit)
        self.unit.matches(x.unit,True)
        return floatUnit(self.value-x.value/self.unit.scale*x.unit.scale,self.unit)

    def __radd__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(x+self.value,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(x.value+self.value,self.unit)
        if self.unit is None:
            return floatUnit(x.value+self.value,x.unit)
        self.unit.matches(x.unit,True)
        return floatUnit(self.value+x.value/self.unit.scale*x.unit.scale,self.unit)

    def __rsub__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(x-self.value,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(x.value-self.value,self.unit)
        if self.unit is None:
            return floatUnit(x.value-self.value,x.unit)
        self.unit.matches(x.unit,True)
        return floatUnit(-(self.value-x.value/self.unit.scale*x.unit.scale),self.unit)

    def __float__(self) -> float:
        return float(self.value)

    def __mul__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value*x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value*x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value*x.value,x.unit)
        return floatUnit(self.value*x.value,self.unit*x.unit)

    def __rmul__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value*x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value*x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value*x.value,x.unit)
        return floatUnit(self.value*x.value,self.unit*x.unit)

    def __truediv__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value/x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value/x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value/x.value,x.unit)
        return floatUnit(self.value/x.value,self.unit/x.unit)

    def __rtruediv__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(x/self.value,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(x.value/self.value,self.unit)
        if self.unit is None:
            return floatUnit(x.value/self.value,x.unit)
        return floatUnit(x.value/self.value,self.unit/x.unit)

    def __floordiv__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value//x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value//x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value//x.value,x.unit)
        return floatUnit(self.value//x.value,self.unit/x.unit)

    def __rfloordiv__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(x//self.value,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(x.value//self.value,self.unit)
        if self.unit is None:
            return floatUnit(x.value//self.value,x.unit)
        return floatUnit(x.value//self.value,self.unit/x.unit)

    def __mod__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(self.value%x,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(self.value%x.value,self.unit)
        if self.unit is None:
            return floatUnit(self.value%x.value,x.unit)
        return floatUnit(self.value%x.value,self.unit/x.unit)

    def __rmod__(self,x:float|int|str|TypeVar('floatUnit')) -> TypeVar('floatUnit'):
        if type(x) in [float,int]:
            return floatUnit(x%self.value,self.unit)
        if isinstance(x,str):
            x = floatUnit(x)
        if x.unit is None:
            return floatUnit(x.value%self.value,self.unit)
        if self.unit is None:
            return floatUnit(x.value%self.value,x.unit)
        return floatUnit(x.value%self.value,self.unit/x.unit)

    def __pow__(self,x:int) -> TypeVar('floatUnit'):
        try:
            n = int(x)
            return floatUnit(self.value**n,self.unit**n)
        except ValueError as err:
            raise UnitException("only int power is allowed") from err

    def __lt__(self,x:float|int|str|TypeVar('floatUnit')) -> bool:
        raise NotImplementedError("TODO")

    def __gt__(self,x:float|int|str|TypeVar('floatUnit')) -> bool:
        raise NotImplementedError("TODO")

    def __le__(self,x:str|TypeVar('Unit')) -> bool:
        raise NotImplementedError("TODO")

    def __ge__(self,x:str|TypeVar('Unit')) -> bool:
        raise NotImplementedError("TODO")

    def __eq__(self,x:str|TypeVar('Unit')) -> bool:
        if isinstance(x,float) or isinstance(x,int):
            return float(x) == self.value
        elif isinstance(x,str):
            x = floatUnit(x)
        if not isinstance(x,type(self)):
            raise TypeError(f"unsupported type {type(x)}")
        if self.unit:
            rtol = 10**-self.unit.prec if self.unit.prec > 0.0 else 0.0
            atol = 10**self.unit.prec if self.unit.prec < 0.0 else 0.0
            if x.unit.prec < 0.0: # absolute precision
                atol = max(atol,10**x.unit.prec)
            elif x.unit.prec > 0.0: # relative precision
                rtol = max(rtol,10**-x.unit.prec)
            x = x.convert(self.unit).value
        else:
            x = x.value
            rtol = 0.0
            atol = 1e-8
        result = math.isclose(self.value,x,rel_tol=rtol,abs_tol=atol)
        return result

    def __ne__(self,x:str|TypeVar('Unit')) -> bool:
        return not self.__eq__(x)

    def convert(self,unit:str|TypeVar('Unit')) -> TypeVar('floatUnit'):
        """Convert value to a different unit

        Arguments:

        * `unit (str|Unit)`: the unit to which the value should be convertor
        """
        if isinstance(unit,str):
            unit = Unit(unit)
        self.unit.matches(unit,True)
        value = (self.value-self.unit.offset) * self.unit.scale / unit.scale + unit.offset
        return floatUnit(round(value,unit.prec),unit)

def test():

    def testEqual(a,b):
        global tested
        tested += 1
        if not a == b:
            global failed
            failed += 1
            print(f"TEST ERROR [unitcalc]: {a} == {b}")

    def testNotEqual(a,b):
        global tested
        tested += 1
        if not a != b:
            global failed
            failed += 1
            print(f"TEST ERROR [unitcalc]: {a} == {b}")

    def testAlmostEqual(a,b,prec=1e-6):
        global tested
        tested += 1
        if abs(float(a-b)) > prec:
            global failed
            failed += 1
            print(f"TEST ERROR [unitcalc]: {a} ~= {b}")

    testEqual(floatUnit("1 Yunit").convert("unit"),1e24)
    testEqual(floatUnit("1 Zunit").convert("unit"),1e21)
    testEqual(floatUnit("1 Eunit").convert("unit"),1e18)
    testEqual(floatUnit("1 Punit").convert("unit"),1e15)
    testEqual(floatUnit("1 Tunit").convert("unit"),1e12)
    testEqual(floatUnit("1 Gunit").convert("unit"),1e9)
    testEqual(floatUnit("1 Munit").convert("unit"),1e6)
    testEqual(floatUnit("1 kunit").convert("unit"),1e3)
    testEqual(floatUnit("1 hunit").convert("unit"),1e2)
    testEqual(floatUnit("1 daunit").convert("unit"),1e1)
    testEqual(floatUnit("1 dunit").convert("unit"),1e-1)
    testEqual(floatUnit("1 cunit").convert("unit"),1e-2)
    testEqual(floatUnit("1 munit").convert("unit"),1e-3)
    testEqual(floatUnit("1 uunit").convert("unit"),1e-6)
    testEqual(floatUnit("1 nunit").convert("unit"),1e-9)
    testEqual(floatUnit("1 punit").convert("unit"),1e-12)
    testEqual(floatUnit("1 funit").convert("unit"),1e-15)
    # note precision of 1 unit is 1e-15
    testEqual(floatUnit("1 aunit"),"1e-18 unit")
    testEqual(floatUnit("1 zunit"),"1e-21 unit")
    testEqual(floatUnit("1 yunit"),"1e-24 unit")

    # area
    testNotEqual(floatUnit("0.999999 m^2"),floatUnit("10.76381 sf"))
    testEqual(floatUnit("1.000000 m^2"),floatUnit("10.76391 sf"))
    testNotEqual(floatUnit("1.000001 m^2"),floatUnit("10.76391 sf"))
    # data rate
    testNotEqual(floatUnit("0.999999 b/s"),floatUnit("1.25e-7 MB/s"))
    testEqual(floatUnit("1.000000 b/s"),floatUnit("1.25e-7 MB/s"))
    testNotEqual(floatUnit("1.000001 b/s"),floatUnit("1.25e-7 MB/s"))
    # data storage
    testNotEqual(floatUnit("0.999999 B"),floatUnit("8 b"))
    testEqual(floatUnit("1.000000 B"),floatUnit("8 b"))
    testNotEqual(floatUnit("1.000001 B"),floatUnit("8 b"))
    # frequency
    testNotEqual(floatUnit("59.99999 unit/s"),floatUnit("60e-3 kHz"))
    testEqual(floatUnit("60.00000 unit/s"),floatUnit("60e-3 kHz"))
    testNotEqual(floatUnit("60.00001 unit/s"),floatUnit("60e-3 kHz"))
    # mileage
    testNotEqual(floatUnit("0.999999 km/l"),floatUnit("2.352146 mile/gal"))
    testEqual(floatUnit("1.000000 km/l"),floatUnit("2.352146 mile/gal"))
    testNotEqual(floatUnit("1.000001 km/l"),floatUnit("2.352146 mile/gal"))
    # energy
    testNotEqual(floatUnit("0.999999 kWh"),floatUnit("3.6 MJ"))
    testEqual(floatUnit("1.000000 kWh"),floatUnit("3.6 MJ"))
    testNotEqual(floatUnit("1.000001 kWh"),floatUnit("3.6 MJ"))
    # distance
    testNotEqual(floatUnit("2.539999 cm"),floatUnit("1 in"))
    testEqual(floatUnit("2.540000 cm"),floatUnit("1 in"))
    testNotEqual(floatUnit("2.540001 cm"),floatUnit("1 in"))
    # mass
    testNotEqual(floatUnit("0.999999 kg"),floatUnit("2.204620 lb"))
    testEqual(floatUnit("1.000000 kg"),floatUnit("2.204620 lb"))
    testNotEqual(floatUnit("1.000001 kg"),floatUnit("2.204620 lb"))
    # angle
    testNotEqual(floatUnit("0.99999999999999 deg"),floatUnit("0.01745328641889982 rad"))
    testEqual(floatUnit("1.00000000000000 deg"),floatUnit("0.01745328641889982 rad"))
    testNotEqual(floatUnit("1.00000000000001 deg"),floatUnit("0.01745328641889982 rad"))
    # pressure
    testNotEqual(floatUnit("0.999999 psi"),floatUnit("6894.757 Pa"))
    testEqual(floatUnit("1.000000 psi"),floatUnit("6894.757 Pa"))
    testNotEqual(floatUnit("1.000001 psi"),floatUnit("6894.757 Pa"))
    # velocity
    testNotEqual(floatUnit("0.999999 mph"),floatUnit("0.4470400 m/s"))
    testEqual(floatUnit("1.000000 mph"),floatUnit("0.4470400 m/s"))
    testNotEqual(floatUnit("1.000001 mph"),floatUnit("0.4470400 m/s"))
    # temperature
    testNotEqual(floatUnit("-0.02 degC"),floatUnit("32 degF"))
    testEqual(floatUnit("+0.00 degC"),floatUnit("32 degF"))
    testNotEqual(floatUnit("+0.02 degC"),floatUnit("32 degF"))
    testNotEqual(floatUnit("273.14 K"),floatUnit("31.98 degF"))
    testEqual(floatUnit("273.14 K"),floatUnit("32.00 degF"))
    testNotEqual(floatUnit("273.14 K"),floatUnit("32.02 degF"))
    # time
    testNotEqual(floatUnit("1 min"),floatUnit("59.99998 s"))
    testEqual(floatUnit("1 min"),floatUnit("60.00000 s"))
    testNotEqual(floatUnit("1 min"),floatUnit("60.00002 s"))
    testNotEqual(floatUnit("1 h"),floatUnit("3599.998 s"))
    testEqual(floatUnit("1 h"),floatUnit("3600.000 s"))
    testNotEqual(floatUnit("1 h"),floatUnit("3600.002 s"))
    # volume
    testNotEqual(floatUnit("0.999999 m^3"),floatUnit("264.17205 gal"))
    testEqual(floatUnit("1.000000 m^3"),floatUnit("264.17205 gal"))
    testNotEqual(floatUnit("1.000001 m^3"),floatUnit("264.17205 gal"))

    x = floatUnit("2.34")
    testAlmostEqual(x,2.34)
    testAlmostEqual(x,"2.34")
    testAlmostEqual(x.value,2.34)
    testAlmostEqual(float(x),2.34)
    testEqual(x.unit,None)
    testEqual(str(x),"2.34")

    x = floatUnit("1.23 m")
    testAlmostEqual(x,1.23)
    testAlmostEqual(x,"1.23 m")
    testAlmostEqual(x,"1230 mm")
    testAlmostEqual(x.value,1.23)
    testAlmostEqual(float(x),1.23)
    testEqual(x.unit,"m")
    testEqual(str(x),"1.23 m")

    x = floatUnit("1.23 m").convert("cm")
    testAlmostEqual(float(x),123.0)
    testEqual(x.unit,"cm")
    testEqual(str(x),"123 cm")

    x = floatUnit("1.23 m")
    y = floatUnit("1 cm")
    z = x + y
    testAlmostEqual(float(z),1.24)
    testEqual(z.unit,"m")
    testEqual(str(z),"1.24 m")

    x = floatUnit("1.23 m")
    y = floatUnit("1 cm")
    z = x - y
    testAlmostEqual(float(z),1.22)
    testEqual(z.unit,"m")
    testEqual(str(z),"1.22 m")

    u = Unit("N*m/s^2")
    testEqual(u._invert(),Unit("s^2/N*m"))

    u = Unit("m/s^2")
    v = Unit("N*s")
    w = u*v
    testEqual(w,Unit("N*m/s"))

    u = Unit("m")
    v = Unit("s")
    testEqual(u/v,Unit("m/s"))

    u = Unit("m")
    testEqual(u*u,u**2)
    testEqual(u*u*u,u**3)
    testEqual(1/u,Unit("/m"))

    return 1 if failed > 0 else 0

if __name__ == "__main__":

    if len(sys.argv) == 1:

        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        exit(1)

    if sys.argv[1] == "test":

        tested = 0
        failed = 0

        exit(test())

    elif sys.argv[1] == 'list':

        print("\n".join([f"{x} = {y}" for x,y in sorted(SPECS.items())]))
        exit(0)

    elif sys.argv[1] in ['help']:

        print(__doc__)
        exit(0)

    try:
        stack = []
        unit = None

        for arg in sys.argv[1:]:

            if arg.startswith("--unit="):

                _,unit = arg.split("=",1)
                unit = unit.split(",")

            elif arg in ['+','add','sum']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)+a] + tail

            elif arg in ['-','sub','subtract','minus']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)-a] + tail

            elif arg in ['*','x','mul','multiply','prod','product']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)*a] + tail

            elif arg in ['/','div','divide']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)/a] + tail

            elif arg in ['//','quot','quotient','floordiv','fdiv']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)//a] + tail

            elif arg in ['%','mod','modulo','rem','remainder']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)%a] + tail

            elif arg in ['^','**','pow','power']:

                a,b = stack[:2]
                tail = stack[2:] if len(stack) > 2 else []
                stack = [floatUnit(b)**a] + tail

            elif arg == "copy": # copy head item

                if len(stack) > 0:
                    stack = [stack[0]] + stack

            elif arg == "ror": # rotate right

                if len(stack) > 1:
                    stack = stack[1:] + [stack[0]]

            elif arg == "rol": # rotate left

                if len(stack) > 1:
                    stack = [stack[-1]] + stack[:-1]

            elif arg in ["rev","reverse"]:

                stack = list(reversed(stack))

            elif arg == "pop": # remove head item

                if len(stack) > 0:
                    stack = stack[1:]

            elif arg in ["swap","exchange"]: # swap top two items

                if len(stack) > 1:
                    stack = [stack[1],stack[0]] + stack[2:]

            else:

                stack.insert(0,arg)

        stack = [x if isinstance(x,floatUnit) else floatUnit(x) for x in reversed(stack)]
        if unit:
            print(",".join([str(x.convert(y)) for x,y in zip(stack,unit)]))
        else:
            print(",".join([str(x) for x in stack]))

    except UnitException as err:

        print(f"ERROR [unitcalc]: {err}")

