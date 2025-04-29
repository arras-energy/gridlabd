
def test_init(obj,t):

    x = gldcore.get_property(obj,"x")
    gldcore.set_double(x,gldcore.get_double(x)+1)

    z = gldcore.get_property(obj,"z")
    gldcore.set_complex(z,gldcore.get_complex(z)+(2+3j))

    i = gldcore.get_property(obj,"i")
    gldcore.set_int64(i,gldcore.get_int64(i)+4)

    j = gldcore.get_property(obj,"j")
    gldcore.set_int32(j,gldcore.get_int32(j)+5)

    k = gldcore.get_property(obj,"k")
    gldcore.set_int16(k,gldcore.get_int16(k)+6)

    b = gldcore.get_property(obj,"b")
    gldcore.set_bool(b,True)

    return 0
