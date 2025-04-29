import sys, gldcore

def on_init(t):
    return True

def test_init(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"1")
    return False

def test_precommit(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"2")
    return gldcore.NEVER

def test_presync(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"3")
    return gldcore.NEVER

def test_sync(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"4")
    return gldcore.NEVER

def test_postsync(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"5")
    return gldcore.NEVER

def test_commit(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"6")
    return gldcore.NEVER

def test_finalize(obj,t):
    gldcore.set_value(obj,"n",gldcore.get_value(obj,"n")+"7")
    return gldcore.NEVER

