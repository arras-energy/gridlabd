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
