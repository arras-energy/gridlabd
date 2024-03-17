import sys

def on_init():
    # print("controllers init ok",file=sys.stderr)
    return True

def on_sync(data):
    # print(f"controllers sync called, data={data}",file=sys.stderr)
    return (int(data['t']/3600)+1)*3600 # advance to top of next hour

def load_control(obj,**kwargs):
    # print(f"load_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800 and kwargs['P'] != 0: # turn off load in first half-hour
        return dict(P=0)
    elif kwargs['t']%3600 >= 1800 and kwargs['P'] == 0: # turn on load in second half-hour
        return dict(P=10)
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)

def powerplant_control(obj,**kwargs):
    # print(f"powerplant_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800 and kwargs['S'].real != 0: # turn off plant in first half-hour
        return dict(S=(0j))
    elif kwargs['t']%3600 >= 1800 and kwargs['S'].real == 0: # turn on plant in second half-hour
        return dict(S=(10+0j))
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)

def relay_control(obj,**kwargs):
    # print(f"relay_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800 and kwargs['status'] != 0: # open the relay in first half-hour
        return dict(status=0)
    elif kwargs['t']%3600 >= 1800 and kwargs['status'] == 0: # close the relay in second half-hour
        return dict(status=1)
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)
