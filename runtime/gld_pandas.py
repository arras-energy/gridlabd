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
    assert file != "", f"{obj=} {file=} is not valid"
    file = open(file,"w")
    interval = int(gldcore.get_value(obj,"interval").split()[0])
    if interval > 0:
        gldcore.set_value(obj,"heartbeat",f"{interval:.0f}")
    timezone = gldcore.get_value(obj,"timezone")
    dtformat = gldcore.get_value(obj,"dtformat")
    source = {}
    for prop in properties:
        try:
            source[prop] = gldcore.property(parent,prop)
        except Exception as err:
            e_type, e_value, _ = sys.exc_info()
            raise e_type(f"{obj}.properties: '{prop}' {e_value}") from err

    recorder[obj] = {
        "file": file,
        "interval": interval,
        "source": source,
        "last": None,
        "timezone": ZoneInfo(timezone) if timezone else None,
        "dtformat": dtformat if dtformat else None,
    }
    file.write(",".join(["timestamp"]+properties)+"\n")
    return gldcore.INIT_OK

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
        if interval >= 0 or row != last:
            recorder[obj]["last"] = list(row)
            tz = recorder[obj]["timezone"];
            ts = datetime.fromtimestamp(t,tz=tz if tz else timezone.utc)
            fmt = recorder[obj]["dtformat"]
            row.insert(0,ts.strftime(fmt) if fmt else ts.isoformat())
            recorder[obj]["file"].write(",".join(row)+"\n")
    return ( t // interval + 1 ) * interval \
        if interval > 0 \
        else gldcore.NEVER

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
    assert properties, f"{obj=} no properties specified"
    source = {}
    for prop in properties:
        try:
            source[prop] = gldcore.property(parent,prop)
        except Exception as err:
            e_type, e_value, _ = sys.exc_info()
            raise e_type(f"{obj}.properties: '{prop}' {e_value}") from err

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

    return gldcore.INIT_OK

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
        prop.set_value(str(data[src]))

    # move to next row
    row += 1
    this["row"] = row
    try:
        tnext = int(this["data"].loc[this["row"],"timestamp"].timestamp())
        return -tnext
    except KeyError:
        return gldcore.NEVER
