[[/Module/Pypower/Transformer]] -- PyPower transformer object

# Synopsis

~~~
class transformer {
    complex impedance[Ohm]; // (REQUIRED) transformer impedance (Ohm)
    double susceptance[S]; // transformer susceptance (S)
    double rated_power[MVA]; // (REQUIRED) transformer power rating (MVA)
    double tap_ratio[pu]; // off-nominal turns ratio (pu)
    double phase_shift[deg]; // transformer phase shift (deg) - use 30 for DY or YD transformers
    enumeration {OUT=0, IN=1} status; // transformer status (IN or OUT)
}
~~~

# Description

The `pypower` module models a `transformer` as a branch whose `status` and
`tap_ratio` properties are updates during `precommit` events. 

The `impedance` must be specified and the real part must be strictly
positive. 

The `susceptance` can be omitted, but must be positive otherwise. 

The transformer rated power is given in `MVA` but it is in fact a `double`. 

The `tap_ratio` specifies the off-nominal turns ratio for tap changing
transformers and must be strictly positive, and a value outside the range 0.8
to 1.2 will produce a warning. Only transformers with `status` value `IN`
will update the branch `turns_ratio`.

The transformer `phase_shift` depends on the type of transformer. Delta-delta
and wye-wye transformers normally have a phase shift of 0 degrees, while
delta-wye and wye-delta transformers normally have a phase shift of 30 degrees.

# Example

The following example defines a delta-delta or wye-wye 100 MW transformer with
an resistance of 10$^{-7}$ Ohm, a reactance of 0.011 Ohm,

~~~
object branch
{
    object transformer
    {
        impedance 1e-07+0.011j Ohm;
        rated_power 100 MVA;
    };
}
~~~

# See Also

* [[Module/Pypower]]
