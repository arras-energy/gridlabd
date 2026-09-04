# recorder.py

import os
import sys
from datetime import datetime, timezone
import pandas as pd

source = {}
recorder = {}
player = {}
dt_format = "%Y-%m-%d %H:%M:%S %Z"

def recorder_init(obj,t):
    """Initialize a recorder"""
    parent = gldcore.get_value(obj,"parent")
    properties = gldcore.get_value(obj,"property").split(",")
    file = gldcore.get_value(obj,"file")
    assert file != "", f"{file=} is not valid"
    file = open(file,"w")
    interval = float(gldcore.get_value(obj,"interval").split()[0])
    flush = gldcore.get_value(obj,"flush")
    source[obj] = {x:gldcore.property(parent,x) for x in properties}
    recorder[obj] = {
        "file": file,
        "interval": interval,
        "flush": flush,
    }
    file.write(",".join(["timestamp"]+properties)+"\n")
    return 0

def recorder_update(obj,t):
    """Update a recorder"""
    row = [datetime.fromtimestamp(t,tz=timezone.utc).strftime(dt_format)]
    for var,prop in source[obj].items():
        value = str(prop)
        row.append(f'"{value}"' if ',' in value else value)
    # TODO: implement flush
    recorder[obj]["file"].write(",".join(row)+"\n")
    return gldcore.NEVER

def player_init(obj,t):
    """TODO"""
    parent = gldcore.get_value(obj,"parent")
    properties = gldcore.get_value(obj,"property").split(",")
    file = gldcore.get_value(obj,"file")
    assert file != "", f"{file=} is not valid"
    player[obj] = {
        "data": pd.read_csv(file,index_col=[0],parse_dates=[0],dtype=float)
    }
    source[obj] = {x:gldcore.property(parent,x) for x in properties}
    return 0

def player_update(obj,t):
    """TODO"""
    return gldcore.NEVER

def on_term(t):
    for obj,param in recorder.items():
        param["file"].close()
    return 0
