
def test_init(obj,t):

    x = gldcore.get_property(obj,"x")
    gldcore.set_double(x,1)
    assert gldcore.get_double(x) == 1, f"double test failed"

    z = gldcore.get_property(obj,"z")
    gldcore.set_complex(z,2+3j)
    assert gldcore.get_complex(z) == 2+3j, f"complex test failed"

    i = gldcore.get_property(obj,"i")
    gldcore.set_int64(i,4)
    assert gldcore.get_int64(i) == 4, f"int64 test failed"

    j = gldcore.get_property(obj,"j")
    gldcore.set_int32(j,5)
    assert gldcore.get_int32(j) == 5, f"int32 test failed"

    k = gldcore.get_property(obj,"k")
    gldcore.set_int16(k,6)
    assert gldcore.get_int16(k) == 6, f"int16 test failed"

    b = gldcore.get_property(obj,"b")
    gldcore.set_bool(b,True)
    assert gldcore.get_bool(b) == True, f"bool test failed"

    return 0
