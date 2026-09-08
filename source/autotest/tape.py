# recorder.py

import os
import sys
import math
from collections import namedtuple
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pytz
from datetime import datetime, timezone
import re
import pandas as pd

sys.path.insert(0,os.environ["GLD_ETC"])
from gld_types import TIMESTAMP

recorder = None
player = None
stream = None

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
DATETIME_SHORT = "%Y-%m-%d %H:%M:%S"
TIMEZONE_LOCALE = None
options = namedtuple("options",["verbose","warning"])(sys.stderr,sys.stderr)

#
# GLOBAL EVENT HANDLERS
#

def on_init(t):
    
    _verbose(f"initializing at {TIMESTAMP(t)}")
    global recorder
    recorder = {}

    global player
    player = {}

    global stream
    stream = {}
    return 1

def on_term(t):
    """Terminate all players"""
    for obj,param in recorder.items():
        param["file"].close()
    return 0

#
# RECORDER CLASS EVENT HANDLERS
#

def recorder_init(obj:str,t:int):
    """Initialize a recorder

    Arguments
    ---------

    - `obj`: object name
    - `t`: initial timestamp

    Returns
    -------

    - `int`: 0 on success, non-zero on failure
    """
    parent = gldcore.get_value(obj,"parent")
    properties = gldcore.get_value(obj,"property").split(",")
    file = gldcore.get_value(obj,"file")
    assert file != "", f"{file=} is not valid"
    file = open(file,"w")
    interval = float(gldcore.get_value(obj,"interval").split()[0])
    flush = gldcore.get_value(obj,"flush")

    recorder[obj] = {
        "file": file,
        "interval": interval,
        "flush": flush,
        "source" : {x:gldcore.property(parent,x) for x in properties}
    }
    file.write(",".join(["timestamp"]+properties)+"\n")
    return 0

def recorder_commit(obj,t):
    """Update a recorder

    Arguments
    ---------

    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------

    - `int`: next timestamp
    """
    row = [datetime.fromtimestamp(t,tz=timezone.utc).strftime(DATETIME_FORMAT)]
    for var,prop in recorder[obj]["source"].items():
        value = str(prop)
        row.append(f'"{value}"' if ',' in value else value)
    # TODO: implement flush
    recorder[obj]["file"].write(",".join(row)+"\n")
    return gldcore.NEVER

#
# PLAYER
#

def player_init(obj,t):
    """Initialize a player

    Arguments
    ---------

    - `obj`: object name
    - `t`: initial timestamp

    Returns
    -------

    - `int`: 0 on success, non-zero on failure
    """

    # get player info
    parent = gldcore.get_value(obj,"parent")
    properties = gldcore.get_value(obj,"property").split(",")
    loop = int(gldcore.get_value(obj,"loop"))
    file = gldcore.get_value(obj,"file")
    dtformat = gldcore.get_value(obj,"dtformat")

    # load data
    assert file != "", f"{file=} is not valid"
    if not file in stream:
        stream[file] = pd.read_csv(file,header=None if properties else 0)
        if file.endswith(".player"):
            stream[file] = _player_to_dataframe(
                stream[file],
                properties=properties,
                dtformat=dtformat,
                loop=loop
                )

    # setup player
    player[obj] = {
        "data": stream[file],
        "row": 0,
        "loop": loop,
        "source": {x:gldcore.property(parent,x) for x in properties}
        }

    return 0

def player_precommit(obj,t):
    """Update a player

    Arguments
    ---------

    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------

    - `int`: next timestamp
    """
    _verbose(f"{t=} <{datetime.fromtimestamp(t)}>")
    this = player[obj]
    row = this["row"]
    _verbose(f"{row=}")
    data = this["data"].loc[row]
    this_timestamp = int(data["timestamp"].timestamp())

    # update time was missed
    if this_timestamp < t:
        _warning(f"missed timestamp {this_timestamp} <{datetime.fromtimestamp(this_timestamp)}>")

    # update time is in the future
    if this_timestamp > t:
        _verbose(f"{this_timestamp=} <{datetime.fromtimestamp(this_timestamp)}>")
        return this_timestamp

    # update time has arrived
    _verbose(f"{data['timestamp']=}")
    for src in this["source"]:
        for item in data:
            _verbose(src,"<-",item)
    this["row"] += 1
    _verbose(f"{this=}")
    tnext = int(this["data"].loc[this["row"],"timestamp"].timestamp())
    _verbose(f"{tnext=} <{datetime.fromtimestamp(tnext)}>")
    return tnext


#
# UTILITIES
#

def _verbose(*args,**kwargs):
    """Output verbose message

    Arguments
    ---------
    - `args`: `print()` non-positional arguments
    - `kwargs`: `print()` positional arguments
    """
    if options.verbose:
        if not "file" in kwargs:
            kwargs["file"] = options.verbose
        print(f"VERBOSE  [{gldcore.get_global('clock')}] (tape.py):", *args,**kwargs)

def _warning(*args,**kwargs):
    """Output a warning message

    Arguments
    ---------
    - `args`: `print()` non-positional arguments
    - `kwargs`: `print()` positional arguments
    """
    if options.warning:
        if not "file" in kwargs:
            kwargs["file"] = options.warning
        print(f"WARNING  [{gldcore.get_global('clock')}] (tape.py): ", *args,**kwargs)

def _timestamp_to_str(t):
    t = TIMESTAMP(t)
    return f"{t=} <{t:%Y-%m-%d %H:%M:%S %Z}>"

def _todatetimetz(
    x:list[str],
    offset:dict[str,str],
    default_timezone:ZoneInfo,
    ) -> datetime:
    """Convert datetime/timezone tuple to a tz-aware datetime

    Arguments
    ---------
    - `x`: (date,time) or (date,time,tz) tuple
    - `offset`: timezone ISO offsets to use when tz is present
    - `default_timezone`: default timezone info to use if tz is missing

    Returns
    -------
    - `datetime`: datetime value localized to utc
    """
    dt = " ".join(x[:2])
    if len(x) > 2: # tz is provided
        return datetime.fromisoformat(dt + offset[x[2]])

    # no tz provided -- use default tzinfo
    dt = datetime.strptime(dt,DATETIME_SHORT)
    dt = dt.replace(tzinfo=default_timezone)

    # _verbose(f"_todatetimetz({x=},{offset=},{default_timezone=}) -> {dt} <{dt.timestamp()}>")

    return dt

def _localize(dt,tz):

    # get global timezone locale info
    global TIMEZONE_LOCALE
    if TIMEZONE_LOCALE is None:
        TIMEZONE_LOCALE = gldcore.get_global("timezone_locale")
    tz_data = re.match("([A-Z]+)([+-]?[0-9]+)([A-Z]+)",TIMEZONE_LOCALE).groups()
    assert len(tz_data) >= 2, "global timezone_locale missing tzoffset"
    default_timezone = ZoneInfo(TIMEZONE_LOCALE)

    std,tzoffset,dst = tz_data[0],math.modf(-float(tz_data[1])),tz_data[2] if len(tz_data) > 2 else None
    offsets = {
        "UTC": "+00:00",
        std: f"{int(tzoffset[1]):+03}:{abs(int(tzoffset[0])*100):02}",
        dst: f"{int(tzoffset[1]+1):+03}:{abs(int(tzoffset[0])*100):02}",
        }

    t = [x.split() for x in dt]

    t = [_todatetimetz(x,offsets,default_timezone) for x in t]
    ts = pd.DatetimeIndex(t,tz=default_timezone)
    return ts.tz_convert(tz)

def _player_to_dataframe(player,
    properties=None,
    dtformat=None,
    loop=None,
    ):
    """Convert a player file into a normalized source dataframe

    Arguments
    ---------
    - `player`: player dataframe
    - `properties`: property name for players with no column headings
    - `dtformat`: alternate date/time format
    - `resample`

    Returns
    -------
    - `pandas.DataFrame`: normalize source dataframe
    """
    if not dtformat:
        dtformat = DATETIME_FORMAT

    df = player.copy()
    df.columns = ["timestamp"] + properties
    df.timestamp = _localize(df.timestamp,timezone.utc)

    starttime = gldcore.get_global("starttime")
    starttime = datetime.strptime(starttime,dtformat).replace(tzinfo=timezone.utc)
    leadup = df[df.timestamp<starttime]
    df.drop(leadup.index[:-1],inplace=True)
    df.loc[leadup.index[-1],"timestamp"] = starttime
    df.sort_values("timestamp",inplace=True)
    df.reset_index(inplace=True,drop=True) # renumber from 0

    if loop: # repeat data
        dt = df.loc[len(df)-1,"timestamp"] - df.loc[0,"timestamp"]
        result = [df]
        for n in range(loop):
            result.append(result[-1].loc[1:].copy())
            result[-1].loc[:,"timestamp"] += dt
        df = pd.concat(result).sort_values("timestamp").reset_index(drop=True)

    return df

if __name__ == '__main__':
    import os
    os.system("cd test_core_player_schedule_1 ; gridlabd.bin test_core_player_schedule_1.glm")
