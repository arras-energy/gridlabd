# recorder
import os
import sys
from datetime import datetime, timezone

recorders = {}
data = []
dt_format = "%Y-%m-%d %H:%M:%S %Z"
def init(obj,t):
    recorders[obj] = {
    	"source": gldcore.get_property(obj,"source"),
    	"signal": gldcore.get_property(obj,"signal"),
    }
    return 0

def update(obj,t):
	item = [datetime.fromtimestamp(t,tz=timezone.utc).strftime(dt_format),obj]
	for var,prop in recorders[obj].items():
		item.append(f"{gldcore.get_double(prop):.4f}")
	data.append(",".join(item))
	return gldcore.NEVER

def on_term(t):
	name = os.path.splitext(os.path.split(gldcore.get_global("modelname"))[1])[0] + ".csv"
	with open(name,"w") as fh:
		fh.write("timesetamp,object,source,signal\n")
		fh.write("\n".join(data))
	return 0