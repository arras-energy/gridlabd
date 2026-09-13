"""GridLAB-D python data types"""

import os
import sys
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, _common

DATETIME_NOTZ = "%Y-%m-%d %H:%M:%S"
"""Default date/time format for timezone-naive timestamps"""

DATETIME_FORMAT = f"{DATETIME_NOTZ} %Z"
"""Default date/time format for timezone-aware timestamps"""

TIMEZONE_LOCALE = None
"""Default timezone locale"""

TZSPECS = {
    "UTC":"+00:00",
    "EDT":"-04:00",
    "EST":"-05:00",
    "CDT":"-05:00",
    "CST":"-06:00",
    "MDT":"-06:00",
    "MST":"-07:00",
    "PDT":"-07:00",
    "PST":"-08:00",
    }
"""Available timezone specifications"""

class TIMESTAMP(int):
    """GridLAB-D TIMESTAMP data type

    A TIMESTAMP is simply an integer that represents the seconds
    of Unix epoch, i.e., since 1/1/1970 00:00:00 UTC.  It supports
    all the usual integer arithmetic with the following caveats:

    - `NEVER` is defined as `2^63-1` and is used to indicate that
      the time is in the infinite future.

    - `INVALID` is defined as `2^64-1` and is used to indicate that
      the time is not valid.

    - `INIT` is defined as `0` and is used to indicate the starting
      time of the simulation

    - A negative value is used to indicate a "soft" time, i.e., a
      time which may be ignored when computing whether a synchronization
      event will occur.
    """
    
    def __new__(cls,t:int|str|None=None):
        """Create a TIMESTAMP 

        Arguments
        ---------
        - `t`: timestamp value, datetime string, or None for global clock value

        Returns
        -------
        - `TIMESTAMP`: TIMESTAMP object
        """
        if isinstance(t,int):

            return super().__new__(cls,t)
        
        if isinstance(t,str):

            dtz = t.split(" ",2)
            match len(dtz):
                case 1:
                    t = datetime.strptime(f"{dtz[0]} 00:00:00",DATETIME_NOTZ).tz_localize(ZoneInfo(TIMEZONE_LOCALE))
                case 2:
                    t = datetime.strptime(f"{dtz[0]} {dtz[1]}",DATETIME_NOTZ).tz_localize(ZoneInfo(TIMEZONE_LOCALE))
                case 3:
                    t = datetime.strptime(f"{dtz[0]} {dtz[1]}{TZSPECS[dtz[2]]}",DATETIME_NOTZ+"%z")
                case _:
                    raise ValueError(f"{t=} is not formatted correctly")
            return super().__new__(cls,t.timestamp())
        
        raise TypeError(f"{t=} is an invalid TIMESTAMP")

    def to_datetime(self) -> datetime:
        """Convert TIMESTAMP to a Python datetime object"""
        return datetime.fromtimestamp(self,tz=timezone.utc)

    def isoformat(self) -> str:
        """Convert TIMESTAMP to ISO date/time string"""
        return self.to_datetime().isoformat()

    def __str__(self):
        """Show a TIMESTAMP in human readable form"""
        return self.to_datetime().strftime(DATETIME_FORMAT)

    def __repr__(self):
        """Show a TIMESTAMP in Python form"""
        return f'TIMESTAMP({int(self)})'

    def __format__(self,spec=None):
        """Format a TIMESTAMP"""
        if spec:
            return self.to_datetime().strftime(spec)
        return str(self)
