# test deferred object initialization
import sys

# global success check variable
OBJECT = None

def init(obj,t):
    """Initialize object with deferral"""

    # check to see if deferral request already done
    if gldcore.get_value(obj,"done") != "TRUE":

        # record deferral in object status `done`
        gldcore.set_value(obj,"done","TRUE")

        # request deferred initialization
        return gldcore.INIT_DEFER

    # record successful deferral
    global OBJECT
    OBJECT = obj

    # initialization complete
    return gldcore.INIT_OK

def on_term(t):

    # check deferral success
    assert OBJECT == "test:0", "deferred initialization failed"
