"""GridLAB-D utilities"""

from dataclasses import dataclass

@dataclass
class MutableData:
    """Class that contain mutable data"""
    def __init__(self, *args, **kwargs):
        """Create a mutable data object

        Arguments
        ---------
        - `*args`: list of keys are initialize as `None`
        - `**wargs`: dict of key values to initialize
        """
        for key in args:
            setattr(self,key,None)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ",".join([f"{x}={repr(getattr(self,x))}" for x in dir(self) if not x.startswith("_")])
        return f"{self.__class__.__name__}({attributes})"

def name_unit(s:str) -> tuple[str,str]:
    """Split a string into a name and its units

    Arguments
    ---------
    - `s`: input string

    Returns
    -------
    - `tuple`: [`name`,`unit`] if input is `name[unit]` where `unit` is 
      `None` if no unit is found
    """
    w = s.strip()
    if "[" in w and w.endswith("]"):
        v,u = w.split("[")
        return [v,u[:-1]]
    return [s,None]

def value_unit(s:str):
    """Split a string into a value and its units
    Arguments
    ---------
    - `s`: input string

    Returns
    -------
    - `tuple`: [`value`,`unit`] if input is `value unit` otherwise [`value`,`None`]
      `None` if no unit is found

    Note that if there is problem converting the value to complex or float, then
    the value is returned as a string.
    """
    def autotype(s):
        try:
            z = complex(s)
            if z.imag == 0:
                return f"{z.real:g}"
            return f"{z.real:g}{z.imag:+g}j"
        except:
            return s

    w = s.strip()
    if " " in w:
        v,u = w.split(" ",1)
        return autotype(v),u
    return autotype(s),None

