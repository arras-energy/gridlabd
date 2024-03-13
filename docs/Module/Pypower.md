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
    enumeration {INIT=0, SUCCESS=1, FAILED=2} solver_status; // Result of the last pypower solver run
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

The following `pypower` data elements are implemented using the corresponding
GridLAB-D `pypower` module classes.

## Bus Objects

~~~
class bus {
    int32 bus_i; // bus number (1 to 29997)
    complex S[MVA]; // base load demand not counting child objects, copied from Pd,Qd by default (MVA)
    enumeration {PQREF=1, NONE=4, REF=3, PV=2, PQ=1, UNKNOWN=0} type; // bus type (1 = PQ, 2 = PV, 3 = ref, 4 = isolated)
    double Pd[MW]; // real power demand (MW)
    double Qd[MVAr]; // reactive power demand (MVAr)
    double Gs[MW]; // shunt conductance (MW at V = 1.0 p.u.)
    double Bs[MVAr]; // shunt susceptance (MVAr at V = 1.0 p.u.)
    int32 area; // area number, 1-100
    double baseKV[kV]; // voltage magnitude (p.u.)
    double Vm[pu*V]; // voltage angle (degrees)
    double Va[deg]; // base voltage (kV)
    int32 zone; // loss zone (1-999)
    double Vmax[pu*V]; // maximum voltage magnitude (p.u.)
    double Vmin[pu*V]; // minimum voltage magnitude (p.u.)
    double lam_P; // Lagrange multiplier on real power mismatch (u/MW)
    double lam_Q; // Lagrange multiplier on reactive power mismatch (u/MVAr)
    double mu_Vmax; // Kuhn-Tucker multiplier on upper voltage limit (u/p.u.)
    double mu_Vmin; // Kuhn-Tucker multiplier on lower voltage limit (u/p.u.)
}
~~~

## Branch Objects

~~~
class branch {
    int32 fbus; // from bus number
    int32 tbus; // to bus number
    double r[pu*Ohm]; // resistance (p.u.)
    double x[pu*Ohm]; // reactance (p.u.)
    double b[pu/Ohm]; // total line charging susceptance (p.u.)
    double rateA[MVA]; // MVA rating A (long term rating)
    double rateB[MVA]; // MVA rating B (short term rating)
    double rateC[MVA]; // MVA rating C (emergency term rating)
    double ratio[pu]; // transformer off nominal turns ratio
    double angle[pu]; // transformer phase shift angle (degrees)
    enumeration {IN=1, OUT=0} status; // initial branch status, 1 - in service, 0 - out of service
    double angmin[deg]; // minimum angle difference, angle(Vf) - angle(Vt) (degrees)
    double angmax[deg]; // maximum angle difference, angle(Vf) - angle(Vt) (degrees)
}
~~~

## Generator Objects

~~~
class gen {
    int32 bus; // bus number
    double Pg[MW]; // real power output (MW)
    double Qg[MVAr]; // reactive power output (MVAr)
    double Qmax[MVAr]; // maximum reactive power output (MVAr)
    double Qmin[MVAr]; // minimum reactive power output (MVAr)
    double Vg[pu*V]; // voltage magnitude setpoint (p.u.)
    double mBase[MVA]; // total MVA base of machine, defaults to baseMVA
    enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} status; // 1 - in service, 0 - out of service
    double Pmax[MW]; // maximum real power output (MW)
    double Pmin[MW]; // minimum real power output (MW)
    double Pc1[MW]; // lower real power output of PQ capability curve (MW)
    double Pc2[MW]; // upper real power output of PQ capability curve (MW)
    double Qc1min[MVAr]; // minimum reactive power output at Pc1 (MVAr)
    double Qc1max[MVAr]; // maximum reactive power output at Pc1 (MVAr)
    double Qc2min[MVAr]; // minimum reactive power output at Pc2 (MVAr)
    double Qc2max[MVAr]; // maximum reactive power output at Pc2 (MVAr)
    double ramp_agc[MW/min]; // ramp rate for load following/AGC (MW/min)
    double ramp_10[MW]; // ramp rate for 10 minute reserves (MW)
    double ramp_30[MW]; // ramp rate for 30 minute reserves (MW)
    double ramp_q[MVAr/min]; // ramp rate for reactive power (2 sec timescale) (MVAr/min)
    double apf; // area participation factor
    double mu_Pmax[pu/MW]; // Kuhn-Tucker multiplier on upper Pg limit (p.u./MW)
    double mu_Pmin[pu/MW]; // Kuhn-Tucker multiplier on lower Pg limit (p.u./MW)
    double mu_Qmax[pu/MVAr]; // Kuhn-Tucker multiplier on upper Qg limit (p.u./MVAr)
    double mu_Qmin[pu/MVAr]; // Kuhn-Tucker multiplier on lower Qg limit (p.u./MVAr)
}
~~~

## Generator Cost Objects

~~~
class gencost {
    enumeration {POLYNOMIAL=2, PIECEWISE=1, UNKNOWN=0} model; // cost model (1=piecewise linear, 2=polynomial)
    double startup[$]; // startup cost ($)
    double shutdown[$]; // shutdown cost($)
    char1024 costs; // cost model (comma-separate values)
}
~~~

# Integration Objects

Integration objects are used to link assets and control models with `pypower`
objects. An integrated object specified its parent `bus` or `gen` object and
updates it as needed prior to solving the powerflow problem.

## Loads

~~~
class load {
    complex S[VA]; // power demand (VA)
    complex Z[Ohm]; // constant impedance load (Ohm)
    complex I[A]; // constant current load (A)
    complex P[VA]; // constant power load (VA)
    complex V[V]; // bus voltage (V)
    double Vn[V]; // nominal voltage (V)
    enumeration {CURTAILED=2, ONLINE=1, OFFLINE=0} status; // load status
    double response[pu]; // curtailment response as fractional load reduction
    char256 controller; // controller python function name
}
~~~

Using the `load` object allows integration of one or more quasi-static load
models with `bus` objects.  The `ZIP` values are used to calculate the `S`
value based on the current voltage. When the load is `ONLINE`, the `S`
value's real and imaginary is then added to the parent `bus` object's `Pd`
and `Qd` values, respectively. When the load is `CURTAILED`, the load is
reduced by the fractional quantity specified by the `response` property. When
the load is `OFFLINE`, the values of `S` is zero regardless of the value of
`P`.

## Powerplants

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

Using `powerplant` objects allows integration of one or more quasi-static
generator models with both `bus` and `gen` objects. When integrating with a
`bus` object, the `S` value real and imaginary values are added to the `bus`
properties `Pd` and `Qd`, respectively, when the plant is `ONLINE`.  

When integrated with a `gen` object, both the `Pd` and `Qd` values are updated
based on the powerplant's generator status and type.

## Powerlines

~~~
class powerline {
    double length[mile]; // (REQUIRED) length (miles)
    complex impedance[Ohm/mile]; // (REQUIRED) line impedance (Ohm/mile)
    enumeration {OUT=0, IN=1} status; // line status (IN or OUT)
    enumeration {PARALLEL=2, SERIES=1} composition; // parent line composition (SERIES or PARALLEL)
}
~~~

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
