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

TODO

# Example

TODO

# See Also

* [[Module/Pypower]]
* [[Module/Pypower/Controllers]]
