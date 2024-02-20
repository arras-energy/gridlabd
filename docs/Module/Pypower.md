[[/Module/Pypower]] -- Module pypower

# Synopsis

GLM:

~~~
module pypower 
{
	set {QUIET=65536, WARNING=131072, DEBUG=262144, VERBOSE=524288} message_flags; // module message control flags
	int32 version; // Version of pypower used
	int32 maximum_timestep; // Maximum timestep allowed between solutions
	double baseMVA[MVA]; // Base MVA value
	bool stop_on_failure; // Flag to stop simulation on solver failure
}
~~~

# Description

The `pypower` module links `gridlabd` with the `pypower` powerflow solver.  The objects used to link the two solvers are supported by the `bus`, `branch`, and `gen` classes.  For details on these
objects' properties, see the [PyPower documentation]([https://pypi.org/project/PYPOWER/).

# See also

* [PyPower documentation]([https://pypi.org/project/PYPOWER/)
* [/Converters/Import/PyPower_cases]
