# recorder.py

import os
import sys
from datetime import datetime, timezone

source = {}
recorder = {}
dt_format = "%Y-%m-%d %H:%M:%S %Z"

def init(obj,t):
    parent = gldcore.get_value(obj,"parent")
    properties = gldcore.get_value(obj,"property").split(",")
    interval = float(gldcore.get_value(obj,"interval").split()[0])
    file = gldcore.get_value(obj,"file")
    assert file != "", f"{file=} is not valid"
    file = open(file,"w")
    flush = gldcore.get_value(obj,"flush")
    source[obj] = {x:gldcore.property(parent,x) for x in properties}
    recorder[obj] = {
        "file": file,
        "interval": interval,
        "flush": flush,
    }
    file.write(",".join(["timestamp"]+properties)+"\n")
    return 0

def update(obj,t):
    row = [datetime.fromtimestamp(t,tz=timezone.utc).strftime(dt_format)]
    for var,prop in source[obj].items():
        value = str(prop)
        row.append(f'"{value}"' if ',' in value else value)
    recorder[obj]["file"].write(",".join(row)+"\n")
    return gldcore.NEVER

def on_term(t):
    for obj,param in recorder.items():
        param["file"].close()
    return 0
