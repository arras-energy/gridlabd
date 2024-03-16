[[/Module/Pypower/Powerplant]] -- PyPower powerplant object

# Synopsis

~~~
class powerplant {
    char32 city; // City in which powerplant is located
    char32 state; // State in which powerplant is located
    char32 zipcode; // Zipcode in which powerplant is located
    char32 country; // Country in which powerplant is located
    char32 naics_code; // Powerplant NAICS code
    char256 naics_description; // Powerplant NAICS description
    int16 plant_code; // Generator plant code number
    set {CC=1024, PV=512, CT=256, ES=128, WT=64, FW=32, IC=16, AT=8, ST=4, HT=2, UNKNOWN=1} generator; // Generator type
    set {NG=32768, COAL=16384, WATER=8192, NUC=4096, GAS=2048, OTHER=1024, WOOD=512, UNKNOWN=256, OIL=128, BIO=64, WASTE=32, COKE=16, GEO=8, SUN=4, WIND=2, ELEC=1} fuel; // Generator fuel type
    enumeration {ONLINE=1, OFFLINE=0} status; // Generator status
    double operating_capacity[MW]; // Generator normal operating capacity (MW)
    double summer_capacity[MW]; // Generator summer operating capacity (MW)
    double winter_capacity[MW]; // Generator winter operating capacity (MW)
    double capacity_factor[pu]; // Generator capacity factor (pu)
    char256 substation_1; // Substation 1 id
    char256 substation_2; // Substation 2 id
    complex S[VA]; // power generation (VA)
    char256 controller; // controller python function name
}
~~~

# Description

Generating units are implemented as `powerplant` objects and requires a parent
`bus` or `gen` object. Each `powerplant` adds its value of `S` to the parent
object's generation output real and reactive power. If the parent object is a
`gen` object, the values of `S.real` and `S.imag` are added to `Pg` and `Qg`,
respectively. If the parent object is a `bus` object, the values are
subtracted from `Pd` and `Qd`, respectively. These updates are completed
during the `presync` event.

During the `sync` event, changed values returned by the `controller` function
are applied to the object, and the next update is schedule at the time `t`
returned by the controller.  Note that unlike the `load` object, `powerplant`
objects do force iteration if no value of `t` is returned.

# Example

The following example implements a 10 kW generator turn turns on only in the
second half of each hour.

`example.glm`:
~~~
#input "case14.py" -t pypower
module pypower
{
    controllers "controllers";
}
object pypower.powerplant
{
    parent pp_bus_2;
    status ONLINE;
    controller "powerplant_control";
}
~~~

`controllers.py`:
~~~
def powerplant_control(obj,**kwargs):
    # print(f"powerplant_control({obj})",kwargs,file=sys.stderr)
    if kwargs['t']%3600 < 1800 and kwargs['S'].real != 0: # turn off plant in first half-hour
        return dict(S=(0j))
    elif kwargs['t']%3600 >= 1800 and kwargs['S'].real == 0: # turn on plant in second half-hour
        return dict(S=(10+0j))
    else: # no change -- advance to next 1/2 hour when a change is anticipated
        return dict(t=(int(kwargs['t']/1800)+1)*1800)
~~~

# See Also

* [[Module/Pypower]]
* [[Module/Pypower/Controllers]]
