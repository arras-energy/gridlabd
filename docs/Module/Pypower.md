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

## Integration Objects

Integration objects are used to link assets and control models with `pypower` objects. 

### Loads

### Generators

### Custom Integrations

To 

# See also

* [PyPower documentation](https://pypi.org/project/PYPOWER/)
* [[/Converters/Import/PyPower_cases]]
