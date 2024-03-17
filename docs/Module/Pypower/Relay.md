[[/Module/Pypower/Relay]] -- PyPower relay object

# Synopsis

~~~
class relay {
    enumeration {OPEN=1, CLOSED=0} status; // relay status (OPEN or CLOSED)
    char256 controller; // controller python function name
}
~~~

# Description

The `relay` object allow direct control a `branch` object using the specified
`controller`.

The `controller` is called during a `sync` event. When `status` is `OPEN` the
`branch` `status` will set to `OUT`. Otherwise the `branch` `status` is set
to `IN`.

# Example

The following example create a relay which is open during the first half-hour
and closed during the second half-hour:

`example.glm`:
~~~
module pypower
{
    controllers "controllers";
}
object branch 
{
    object relay
    {
        controller "relay_control";
    };
}
~~~

`controllers.py`:
~~~
def relay_control(obj,**kwargs):
    if kwargs['t']%3600 < 1800 and kwargs['status'] != 0: # open the relay in first half-hour
        return dict(status=0) # omitting 't' forces iteration
    elif kwargs['t']%3600 >= 1800 and kwargs['status'] == 0: # close the relay in second half-hour
        return dict(status=1) # omitting 't' forces iteration
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)
~~~

# See Also

* [[Module/Pypower]]
