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
}
~~~

# Description

The `pypower` module links `gridlabd` with the `pypower` powerflow solver.  The objects used to link the two solvers are supported by the `bus`, `branch`, and `gen` classes.  For details on these
objects' properties, see the [PyPower documentation]([https://pypi.org/project/PYPOWER/).

If `enable_opf` is `TRUE`, then the OPF solver is used when `gencost` objects are defined.

If `save_case` is `TRUE`, then the case data and solver results are stored in `pypower_casedata.py` and `pypower_results.py` files.

# Integration Objects

Integration objects are used to link assets and control models with `pypower` objects. An integrated object specified its parent `bus` or `gen` object and updates it as needed prior to solving the powerflow problem.

## Loads

Using the `load` object allows integration of one or more quasi-static load models with `bus` objects.  The `ZIP` values are used to calculate the `S` value based on the current voltage. When the load is `ONLINE`, the `S` value's real and imaginary is then added to the parent `bus` object's `Pd` and `Qd` values, respectively. When the load is `CURTAILED`, the load is reduced by the fractional quantity specified by the `response` property. When the load is `OFFLINE`, the values of `S` is zero regardless of the value of `P`.

## Powerplants

Using the `powerplant` objects allows integration of one or more quasi-static generator models with both `bus` and `gen` objects. When integrating with a `bus` object, the `S` value real and imaginary values are added to the `bus` properties `Pd` and `Qd`, respectively, when the plant is `ONLINE`.  

When integrated with a `gen` object, both the `Pd` and `Qd` values are updated based on the powerplant's generator status and type.

## Controls

TODO

## Custom Integrations

TODO

# See also

* [PyPower documentation](https://pypi.org/project/PYPOWER/)
* [[/Converters/Import/PyPower_cases]]
