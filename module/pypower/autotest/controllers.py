import sys

def on_init():
    # print("controllers init ok",file=sys.stderr)
    return True

def load_control(obj,**kwargs):
    print(obj,": load control update",kwargs,file=sys.stderr)
    return dict(t=kwargs['t']+3600, S=(15+2j))

def powerplant_control(obj,**kwargs):
    print(obj,": powerplant control update",kwargs,file=sys.stderr)
    return dict(t=kwargs['t']+3600, S="15+2j kW")
