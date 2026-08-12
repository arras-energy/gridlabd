import os
import sys

recorders = {}
data = []

def init(obj,t):
    recorders[obj] = {
    	"source": gldcore.get_property(obj,"source"),
    	"signal": gldcore.get_property(obj,"signal"),
    }
    return 0

def update(obj,t):
	item = [str(t)]
	for var,prop in recorders[obj].items():
		item.append(str(gldcore.get_double(prop)))
	data.append(",".join(item))
	return gldcore.NEVER

def finish(obj,t):
	name = os.path.splitext(os.path.split(gldcore.get_global("modelname"))[1])[0] + ".csv"
	with open(name,"w") as fh:
		fh.write("\n".join(data))
	return 0