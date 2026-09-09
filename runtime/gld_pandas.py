"""GridLAB-D Pandas Module"""

import os
import sys
import math
from collections import namedtuple
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import re

import pandas as pd

from gld_timestamp import TIMESTAMP
from gld_output import verbose, warning
import gld_output

gld_output.options.modulename = os.path.basename(__file__)

recorder = None
player = None

#
# GLOBAL EVENT HANDLERS
#

def on_init(t):
    
    global recorder
    recorder = {}

    global player
    player = {}

    return 1

def on_term(t):
    """Terminate all players"""
    for obj,param in recorder.items():
        param["file"].close()

    return None

#
# RECORDER CLASS EVENT HANDLERS
#

def recorder_init(obj:str,t:int) -> int:
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
    interval = int(gldcore.get_value(obj,"interval").split()[0])
    if interval > 0:
        gldcore.set_value(obj,"heartbeat",f"{interval:.0f}")

    recorder[obj] = {
        "file": file,
        "interval": interval,
        "source": {x:gldcore.property(parent,x) for x in properties},
        "last": None,
    }
    file.write(",".join(["timestamp"]+properties)+"\n")
    return 0

def recorder_commit(obj:str,t:int) -> int:
    """Update a recorder

    Arguments
    ---------

    - `obj`: object name
    - `t`: current timestamp

    Returns
    -------

    - `int`: next timestamp
    """
    interval = int(recorder[obj]["interval"])
    if interval <= 0 or t % interval == 0: # time to sample values
        row = []
        for var,prop in recorder[obj]["source"].items():
            value = str(prop)
            row.append(f'"{value}"' if ',' in value else value)
        last = recorder[obj]["last"]
        verbose(f"{row=} {last=}")
        if interval >= 0 or row != last:
            recorder[obj]["last"] = list(row)
            row.insert(0,datetime.fromtimestamp(t,tz=timezone.utc).isoformat())
            recorder[obj]["file"].write(",".join(row)+"\n")
    return ( t // interval + 1 ) * interval if interval > 0 else gldcore.NEVER

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

    properties = [x.strip() for x in gldcore.get_value(obj,"property").split(",") if x != ""]

    file = gldcore.get_value(obj,"file")
    data = pd.read_csv(file,
        parse_dates=["timestamp"] if properties else True,
        header=None if properties else 0,
        usecols=["timestamp"]+properties if properties else None,
        names=["timestamp"]+properties if properties else None,
        converters={x:str for x in properties} if properties else None,
        dtype=None if properties else str,
        )

    if not properties:
        properties = data.columns[1:].tolist()
    assert properties, "no properties specified"
    source = {x:gldcore.property(parent,x) for x in properties}

    try:
        timezone = gldcore.get_value(obj,"timezone")
        data.timestamp = pd.DatetimeIndex(data.timestamp).tz_localize(timezone if timezone else "UTC")
    except:
        data.timestamp = pd.DatetimeIndex(data.timestamp).tz_convert("UTC")

    # setup player
    player[obj] = {
        "data": data,
        "row": 0,
        "source": source,
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
    this = player[obj]
    row = this["row"]
    try:
        data = this["data"].loc[row]
    except KeyError:
        return gldcore.NEVER

    this_timestamp = int(data["timestamp"].timestamp())

    # update time was missed
    if this_timestamp < t:
        warning(f"missed timestamp {this_timestamp} <{datetime.fromtimestamp(this_timestamp)}>")

    # update time is in the future
    if this_timestamp > t:
        return this_timestamp

    # update time has arrived
    for src,prop in this["source"].items():
        for item in data[1:]:
            prop.set_value(item)

    # move to next row
    row += 1
    this["row"] = row
    try:
        tnext = int(this["data"].loc[this["row"],"timestamp"].timestamp())
        return -tnext
    except KeyError:
        return gldcore.NEVER
