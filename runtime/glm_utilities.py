"""GridLAB-D utilities"""

from datetime import datetime
from dataclasses import dataclass
from typing import Any

@dataclass
class MutableData:
    """Class that contains mutable data"""
    def __init__(self, *args, **kwargs):
        """Create a mutable data object

        Arguments
        ---------
        - `*args`: list of keys are initialize as `None`
        - `**wargs`: dict of key values to initialize

        Example
        -------

        The command

            data = MutableData("a","b",c=123,d='abc')
            data.b = 4.56
            print(data)

        outputs

            MutableData(a=None,b=4.56,c=123,d='abc')
        """
        for key in args:
            setattr(self,key,None)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ",".join([f"{x}={repr(y)}" for x,y in self.aslist()])
        return f"{self.__class__.__name__}({attributes})"

    def aslist(self) -> list[tuple[str,Any]]:
        """Return data as a list of tuples

        Returns
        -------
        - `list`: list of data item tuples
        """
        return [(x,getattr(self,x)) for x in dir(self) if not x.startswith("_") and not callable(getattr(self,x))]
    def asdict(self) -> dict:
        """Return data as a dict

        Returns
        -------
        - `dict`: dict of data item keys and values
        """
        return dict(self.aslist())

def name_unit(s:str) -> tuple[str,str]:
    """Split a string into a name and its units

    Arguments
    ---------
    - `s`: input string

    Returns
    -------
    - `tuple`: [`name`,`unit`] if input is `name[unit]` where `unit` is 
      `None` if no unit is found

    Example
    -------

    The command

        name_unit("time[s]")

    returns

        ["time","s"]
    """
    w = s.strip()
    if "[" in w and w.endswith("]"):
        v,u = w.split("[")
        return [v,u[:-1]]
    return [s,None]

def value_unit(
    s:str,
    autotype=False,
    nofail=False,
    ):
    """Split a string into a value and its units

    For 
    Arguments
    ---------
    - `s`: input string
    - `autotype`: enable automatic conversion to float or complex
    - `nofail`: raise exception on autotype failure instead of returning
      `str`

    Returns
    -------
    - `tuple`: [`value`,`unit`] if input is `value unit` otherwise [`value`,`None`]
      `None` if no unit is found

    Example
    -------

    The command

        value_unit("1.23 MW",autotype=True)

    returns

        (1.23,"MW")

    Caveat
    ------

    If there is error converting the value to complex or float, then the value
    is always returned as a string rather than returned as a float or double
    when `autotype` is `True`. Use `nofail=True` to raise the exception
    instead.
    """
    def _autotype(s):
        try:
            z = complex(s)
            if z.imag == 0:
                return z.real if autotype else f"{z.real:g}"
            return z if autotype else f"{z.real:g}{z.imag:+g}j"
        except ValueError:
            if nofail:
                raise
            return s

    w = s.strip()
    if " " in w:
        v,u = w.split(" ",1)
        return _autotype(v),u
    return _autotype(s),None

def autotype(
    x:str,
    allow=[int,float,complex,datetime,str],
    nodefault:bool=False
    ) -> int|float|complex|datetime|str:
    """Automatically change type of GridLAB-D data

    Arguments
    ---------

    Returns
    -------
    - `int`:
    - `float`:
    - `complex`:
    - `datetime`:
    - `str`:
    """
    if int in allow:
        try:
            return int(x)
        except ValueError:
            pass

    if float in allow:
        try:
            return float(x)
        except ValueError:
            pass

    if complex in allow:
        try:
            return complex(x)
        except ValueError:
            pass

    if datetime in allow:
        try:
            return datetime.fromisoformat(x)
        except ValueError:
            return x

    if nodefault:
        raise ValueError(f"autotype({repr(x)}) failed")

    return str(x)

