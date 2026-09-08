# recorder.py

import os
import sys
import math
from collections import namedtuple
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import re
import pandas as pd

recorder = None
player = None
stream = None

MODULE_NAME = os.path.basename(__file__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
DATETIME_SHORT = "%Y-%m-%d %H:%M:%S"
TIMEZONE_LOCALE = None

options = namedtuple("options",["verbose","warning"])(sys.stderr,sys.stderr)

#
# GLOBAL EVENT HANDLERS
#

def on_init(t):
    
    _verbose(f"initializing at {t}")
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
        print(f"VERBOSE  [{gldcore.get_global('clock')}] ({MODULE_NAME}):", *args,**kwargs)

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
        print(f"WARNING  [{gldcore.get_global('clock')}] ({MODULE_NAME}): ", *args,**kwargs)

def _timestamp_to_str(t):
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S %Z")

if __name__ == '__main__':
    import os
    os.system("gridlabd pandas.glm")
