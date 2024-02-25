import sys

def on_init():
    return True

def load_control(obj,**kwargs):
    print(obj,"load control update",kwargs,file=sys.stderr)
    return {}

def powerplant_control(obj,**kwargs):
    print(obj,"powerplant control update",kwargs,file=sys.stderr)
    return {}
