[[/Module/Pypower/Scada]] -- PyPower SCADA object

# Synopsis

~~~
class scada {
    method point; // Enable access to point specified as object <name>:<property>
    bool write; // Enable write to point
    bool record; // Enable recording of point to historian
}
~~~

# Description

The `scada` object enables reading and writing properties of objects from the
`controllers` file. When a `scada` object is defined, the `scada` and
`historian` dictionaries is added to the `controllers` globals.  Each
dictionary contains a key entry for each `scada` object defined. The key is
the name of the object.  The `scada` object contains the current values of
each item listed in the `point` properties. Multiple points may be defined in
each `scada` object and multiple `scada` objects may be defined in a single
model.

The `historian` object contains copies of past `scada` dictionaries keyed by
timestamp for all `scada` objects for which `record` is `TRUE`.

If the `scada` object has the value `write` set to `TRUE`, then any changes
to the `scada` dictionary will be copied back to the original object.

# Example

`example.glm`:
~~~
#input "case14.py" -t pypower
module pypower
{
    controllers "controllers";
}
clock
{
    starttime "2020-01-01 00:00:00";
    stoptime "2020-01-02 00:00:00";
}
object scada
{
    point pp_bus_1.Vm;
    point pp_bus_1.Va;
}
~~~

`controllers.py`:
~~~
import sys
def on_sync(data):
    print(data['t'],scada,file=sys.stderr)
~~~

# See Also

* [[Module/Pypower]]
