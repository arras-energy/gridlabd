import sys

def on_init():
    # print("controllers init ok",file=sys.stderr)
    return True

def on_sync(data):
    # print(f"controllers sync called, data={data}",file=sys.stderr)
    return (int(data['t']/3600)+1)*3600 # advance to top of next hour

def load_control(obj,**kwargs):
    # print(obj,": load control update",kwargs,file=sys.stderr)
    return dict(t=kwargs['t']+3600, S=(15+2j))

def powerplant_control(obj,**kwargs):
    # print(obj,": powerplant control update",kwargs,file=sys.stderr)
    return dict(t=kwargs['t']+3600, S="15+2j kW")
