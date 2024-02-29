[[/Module/Pypower]] -- Module pypower

# Synopsis

GLM:

~~~
module pypower 
{
    set {QUIET=65536, WARNING=131072, DEBUG=262144, VERBOSE=524288} message_flags; // module message control flags
    int32 version; // Version of pypower used (default is 2)
    enumeration {NR=1, FD_XB=2, FD_BX=3, GS=4} solver_method; // PyPower solver method to use
    int32 maximum_timestep; // Maximum timestep allowed between solutions (default is 0, meaning no maximum timestep)
    double baseMVA[MVA]; // Base MVA value (default is 100 MVA)
    bool enable_opf; // Flag to enable solving optimal powerflow problem instead of just powerflow (default is FALSE)
    bool stop_on_failure; // Flag to stop simulation on solver failure (default is FALSE)
    bool save_case; // Flag to enable saving case data and results (default is FALSE)
    char1024 controllers; // Python module containing controller functions
    double solver_update_resolution; // Minimum difference before a value is considered changed
}
~~~

# Description

The `pypower` module links `gridlabd` with the `pypower` powerflow solver. The
objects used to link the two solvers are supported by the `bus`, `branch`,
and `gen` classes.  For details on these objects' properties, see the
[PyPower documentation]([https://pypi.org/project/PYPOWER/).

If `enable_opf` is `TRUE`, then the OPF solver is used when `gencost` objects
are defined.

If `save_case` is `TRUE`, then the case data and solver results are stored in
`pypower_casedata.py` and `pypower_results.py` files.

If you have convergence iteration limit issues when larger models, try
increasing the value of `solver_update_resolution`.  The larger this value
is, the larger a difference between an old value and new value from the
solver must be to be considered a change necessitating additional iteration.
The default value is `1e-8`, which should be sufficient for most models.


# Integration Objects

Integration objects are used to link assets and control models with `pypower`
objects. An integrated object specified its parent `bus` or `gen` object and
updates it as needed prior to solving the powerflow problem.

## Loads

Using the `load` object allows integration of one or more quasi-static load
models with `bus` objects.  The `ZIP` values are used to calculate the `S`
value based on the current voltage. When the load is `ONLINE`, the `S`
value's real and imaginary is then added to the parent `bus` object's `Pd`
and `Qd` values, respectively. When the load is `CURTAILED`, the load is
reduced by the fractional quantity specified by the `response` property. When
the load is `OFFLINE`, the values of `S` is zero regardless of the value of
`P`.

## Powerplants

Using `powerplant` objects allows integration of one or more quasi-static
generator models with both `bus` and `gen` objects. When integrating with a
`bus` object, the `S` value real and imaginary values are added to the `bus`
properties `Pd` and `Qd`, respectively, when the plant is `ONLINE`.  

When integrated with a `gen` object, both the `Pd` and `Qd` values are updated
based on the powerplant's generator status and type.

## Powerlines

Using `powerline` object allows composite lines to be constructed and
assembled into `branch` objects.  A `powerline` may either have a `branch`
parent or another `powerline` object, in which case the parent must specify
whether its `composition` is either `SERIES` or `PARALLEL`.  When a
`powerline` is not a composite line you must specify its `impedance` in Ohms
per mile and its length in `miles`. Only lines with `status` values `IN` are
assembled in the parent line. Line with `status` values `OUT` are ignored. 

The `status` value, `impedance`, `length`, and `composition` may be changed at
any time during a simulation. However, these values are only checked for
consistency and sanity during initialization.

## Controllers

Controllers may be added by specifying the `controllers` global in the
`pypower` module globals, e.g.,

~~~
module pypower
{
    controllers "my_controllers";
}
~~~

This will load the file `my_controllers.py` and link the functions defined in
it.

If the `on_init` function is defined in the Python `controllers` module, it
will be called when the simulation is initialized. Note that many `gridlabd`
module functions are not available until after initialization is completed.

Any `load` or `powerplant` object may specify a `controller` property. When
this property is defined, the corresponding controller function will be
called if it is defined in the `controllers` module.

Controller functions use the following call/return prototype

~~~
def my_controller(obj,**kwargs):
    return dict(name=value,...)
~~~

where `kwargs` contains a dictionary of properties for the object and `name`
is any valid property of the calling object. A special return name `t` is
used to specify the time at which the controller is to be called again,
specify in second of the Unix epoch.

# See also

* [PyPower documentation](https://pypi.org/project/PYPOWER/)
* [[/Converters/Import/PyPower_cases]]
