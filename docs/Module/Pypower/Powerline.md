[[/Module/Pypower/Powerline]] -- PyPower powerline object

# Synopsis

~~~
class powerline {
    double length[mile]; // (REQUIRED) length (miles)
    complex impedance[Ohm/mile]; // (REQUIRED) line impedance (Ohm/mile)
    enumeration {OUT=0, IN=1} status; // line status (IN or OUT)
    enumeration {PARALLEL=2, SERIES=1} composition; // parent line composition (SERIES or PARALLEL)
}
~~~

# Description

Pypower `branch` object can comprise one or more `powerline` objects using a
combination of parallel and series lines. Line composition is determined
using the `parent` properties of a `powerline` object.  The top-level
`powerline` must the only child of a `branch`. Each `powerline` object may
specify whether it's child `powerline` objects are in parallel or series
using the `composition` property.  

At initialization the `impedance` and `length` values are used to calculate
the `powerline` object's `Z` and `Y` values.

All `powerline` compositions are updated during `precommit` events using the
`Z` and `Y` values to generate the `r`, `x`, and `b` properties of the parent
`branch`.  Each `powerline` object will be included in the composition only
if `status` is `IN`.

# Example

The following example illustrates a simple powerline definition:

~~~
object branch 
{
    object powerline
    {
        impedance 0.01938+0.05917j mOhm/mile;
        susceptance 0.0528 mS/mile;
        length 1000 mile;
    };
}
~~~

The following example illustrates a series powerline composition:
~~~
object branch
{
    object powerline 
    {
        composition SERIES;
        object powerline 
        {
            impedance 0.05403+0.22304j mOhm/mile;
            susceptance 0.0492 mS/mile;
            length 500 mile;
        };
        object powerline 
        {
            impedance 0.05403+0.22304j mOhm/mile;
            susceptance 0.0492 mS/mile;
            length 500 mile;
        };
    };
}
~~~

The following example illustrates a parallel powerline composition:

~~~
object branch
{
    object powerline 
    {
        composition PARALLEL;
        object powerline 
        {
            impedance 0.04699+0.19797j mOhm/mile;
            susceptance 0.0438 mS/mile;
            length 2000 mile;
        };
        object powerline 
        {
            impedance 0.04699+0.19797j mOhm/mile;
            susceptance 0.0438 mS/mile;
            length 2000 mile;
        };
    };
}
~~~

# See Also

* [[Module/Pypower]]
* [[Module/Pypower/Controllers]]
