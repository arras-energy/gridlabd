[[/Module/Pypower/Transformer]] -- PyPower transformer object

# Synopsis

~~~
class transformer {
    complex impedance[Ohm]; // (REQUIRED) transformer impedance (Ohm)
    enumeration {OUT=0, IN=1} status; // transformer status (IN or OUT)
    double phase_shift[deg]; // transformer phase shift (deg) - use 30 for DY or YD transformers
    double rated_power[MVA]; // (REQUIRED) transformer power rating (MVA)
    double primary_voltage[kV]; // primary winding nominal voltage (kV)
    double secondary_voltage[kV]; // secondary winding nominal_voltage (kV)
}
~~~

# Description

TODO

# Example

TODO

# See Also

* [[Module/Pypower]]
* [[Module/Pypower/Controllers]]
