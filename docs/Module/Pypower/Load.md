[[/Module/Pypower/Load]] -- PyPower load object

# Synopsis

~~~
class load {
    complex S[MVA]; // power demand (MVA)
    complex Z[MVA]; // constant impedance load (MVA)
    complex I[MVA]; // constant current load (MVA)
    complex P[MVA]; // constant power load (MVA)
    complex V[kV]; // bus voltage (kV)
    double Vn[kV]; // nominal voltage (kV)
    enumeration {CURTAILED=2, ONLINE=1, OFFLINE=0} status; // load status
    double response[pu]; // curtailment response as fractional load reduction
    char256 controller; // controller python function name
}
~~~

# Description

Every `load` object must have a `bus` object as a parent. Each `load` object
adds `S` to the `Pd` and `Qd` values for the parent bus during the `presync`
event if `status` is not `OFFLINE`. The values of `Pd` is taken from the real
part of `S` and `Qd` from the imaginary part of `S`. The value of `S` is
computed based on the values of `Z`, `I`, and `P`, the constant impedance,
current, and power values, respectively and the voltage of the bus. If the
`status` is `CURTAILED`, the value of `S` is multiplied by the value
`response`.

During the `sync` event the values of any property may be changes by the
`controller` function, if it is specified. If the controller changes any
properties this will cause iteration if `t` is not specified in the controller
return value.

During the `postsync` event the value of the bus voltage magnitude `Vm` and
angle `Va` are copied to the load voltage `V`.

# Example

The following example implements a constant power load at 10kW that turns on
only in the second half of each hour.

`example.glm`:
~~~
#input "case14.py" -t pypower
module pypower
{
    controllers "controllers";
}
object pypower.load
{
    parent pp_bus_2;
    status ONLINE;
    controller "load_control";
}
~~~

`controllers.py`:
~~~
def load_control(obj,**kwargs):
    if kwargs['t']%3600 < 1800 and kwargs['P'] != 0: # turn off load in first half-hour
        return dict(P=0) # omitted 't' causes iteration
    elif kwargs['t']%3600 >= 1800 and kwargs['P'] == 0: # turn on load in second half-hour
        return dict(P=10) # omitted 't' causes iteration
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)
~~~

# See Also

* [[Module/Pypower]]
* [[Module/Pypower/Controllers]]
