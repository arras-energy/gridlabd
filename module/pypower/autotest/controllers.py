import sys

def on_init():
    # print("controllers init ok",file=sys.stderr)
    return True

def on_sync(data):
    # print(f"controllers sync called, data={data}",file=sys.stderr)
    # print(scada,historian,file=sys.stderr)
    return (int(data['t']/3600)+1)*3600 # advance to top of next hour

def load_control(obj,**kwargs):
    # print(f"load_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800 and kwargs['P'] != 0: # turn off load in first half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,P=0)
    elif kwargs['t']%3600 >= 1800 and kwargs['P'] == 0: # turn on load in second half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,P=10)
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)

def powerplant_control(obj,**kwargs):
    # print(f"powerplant_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800: # turn off plant in first half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,S=(0j))
    elif kwargs['t']%3600 >= 1800: # turn on plant in second half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,S=(10+0j))
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)

def storage_control(obj,**kwargs):
    # print(f"powerplant_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800: # discharge in first half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,S=(-0.001+0j))
    elif kwargs['t']%3600 >= 1800: # charge in second half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,S=(0.01+0j))
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)

def relay_control(obj,**kwargs):
    # print(f"relay_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800 and kwargs['status'] != 0: # open the relay in first half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,status=0)
    elif kwargs['t']%3600 >= 1800 and kwargs['status'] == 0: # close the relay in second half-hour
        return dict(t=(int(kwargs['t']/1800)+1)*1800,status=1)
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)
