"""GridLAB-D python data types"""

import os
import sys
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, _common

DATETIME_NOTZ = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT = f"{DATETIME_NOTZ} %Z"
TIMEZONE_LOCALE = None
TZSPECS = {
    "UTC":"+00:00",
    }

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

            global TIMEZONE_LOCALE
            if TIMEZONE_LOCALE is None:
                TIMEZONE_LOCALE = gldcore.get_global("timezone_locale")
            try:
                default_timezone = ZoneInfo(TIMEZONE_LOCALE)
                print(default_timezone.tzname(),default_timezone.utcoffset())
            except _common.ZoneInfoNotFoundError:
                tz_data = list(re.match(r"([A-Z]+)([+-]?[0-9\.]+)?([A-Z]+)?",TIMEZONE_LOCALE).groups())
                if tz_data[0] == "UTC":
                    if tz_data[1] is None:
                        tz_data[1] = 0.0
                    assert float(tz_data[1]) == 0.0, "UTC can only have offset 0"
                    assert tz_data[2] is None, "UTC cannot have summer time"
                else:
                    tz_data[1] = float(tz_data[1])
                std,tzoffset,dst = tz_data

            dtz = t.split()
            match len(dtz):
                case 1:
                    dtz.extend(["00:00:00",TZSPECS[TIMEZONE_LOCALE]])
                case 2:
                    dtz.append(TZSPECS[TIMEZONE_LOCALE])
                case 3:
                    dtz[2] = TZSPECS[TIMEZONE_LOCALE]
                case _:
                    raise ValueError(f"{t=} is not formatted correctly")
            t = f"{dtz[0]}T{dtz[1]}{dtz[2]}"
            return super().__new__(cls,datetime.fromisoformat(t).timestamp())

        if t is None:
            
            return TIMESTAMP(gldcore.get_global("clock"))
        
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

if __name__ == '__main__':

    class gldcore:
        """Test rig for gridlabd globals"""
        GLOBALS = {
            "timezone_locale": "UTC",
            "clock": 946684800,
        }

        @classmethod
        def get_global(cls,name):
            return cls.GLOBALS[name]

    t = TIMESTAMP("2000-01-01 00:00:00")

    assert str(t) == "2000-01-01 00:00:00 UTC"
    assert repr(t) == "TIMESTAMP(946684800)"
    assert t.isoformat() == "2000-01-01T00:00:00+00:00"
    assert f"{t}" == "2000-01-01 00:00:00 UTC"
    assert f"{t=}" == "t=TIMESTAMP(946684800)"
    assert f"{t:%m/%d/%Y %H:%M:%S}" == "01/01/2000 00:00:00"

    TIMEZONE_LOCALE = "UTC"

    t = TIMESTAMP("2000-01-01 00:00:00")

    assert str(t) == "2000-01-01 00:00:00 UTC"
    assert repr(t) == "TIMESTAMP(946684800)"
    assert t.isoformat() == "2000-01-01T00:00:00+00:00"
    assert f"{t}" == "2000-01-01 00:00:00 UTC"
    assert f"{t=}" == "t=TIMESTAMP(946684800)"
    assert f"{t:%m/%d/%Y %H:%M:%S}" == "01/01/2000 00:00:00"

    t = TIMESTAMP("2000-01-01 00:00:00 UTC")

    TIMEZONE_LOCALE = "PST+8PDT"
    t = TIMESTAMP("1999-12-31 16:00:00 PST")

    TIMEZONE_LOCALE = "America/Los_Angeles"
    t = TIMESTAMP("1999-12-31 16:00:00 PST")
