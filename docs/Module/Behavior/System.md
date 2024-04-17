[[/Module/Behavior/System]] - Random discrete behavior

# Synopsis

~~~
module behavior {
    set {QUIET=65536, WARNING=131072, DEBUG=262144, VERBOSE=524288} message_flags; // module message control flags
    double system_resolution; // Resolution of system properties
}
class system {
    double tau; // System activity
    double mu; // Asset potential
    int64 N; // Number of devices
    int64 N0; // Number of sites
    method u; // State values
    method q; // State quantities
    method device; // Property of device connected to this system
    double U; // (OUTPUT) Total value of all states
    double sigma; // (OUTPUT) System entropy
    method p; // (OUTPUT) State probabilities
    double Z; // (OUTPUT) State partition function
    double F; // (OUTPUT) Free value
    double P; // (OUTPUT) Internal price
    double Q; // (OUTPUT) Total quantity
    double Nexp; // (OUTPUT) Expected number of devices
    double Uexp; // (OUTPUT) Expected device value
    double Qexp; // (OUTPUT) Expected quantity
    double chi; // (OUTPUT) Price susceptibility (dQ/dP)
    double Cp; // (OUTPUT) Value capacity (dU/dtau)
}
~~~

# Description

The `system` object implements a statistical mechanics-inspired model of the
aggregate properties of systems of devices that behave in accordance with
principles that are analogous to those in thermodynamics, i.e.,

1. If two systems are in equilibrium with a third system, then they are in
equilibrium with each other.

2. In a closed system any change in internal value is equal to the value added
to the system minus the value removed from it. When two system are connected,
the total internal value of the combined system is the sum of the internal
values of the separate systems.

3. When two separate systems at internal equilibrium are connected, then when
they come to equilibrium the sum of their separate entropies at equilibrium
is less than or equal to the total entropy of the connected systems.

4. The system's entropy approaches a constant value as the system's activity
`tau` approach zero.

The follow analogies to thermodynamics are used in the generalization of the model:

* *number of devices* `N`: This is equivalent to the number of particles.
* *value* `u`: This is equivalent to energy.
* *activity* `tau`: This is equivalent to absolute temperature.
* *asset potential* `mu`: This is equivalent to chemical potential.
* *quantity* `q` is equivalent to magnetic moment.
* *price* `P` is equivalent to magnetic field.

The values of outputs are updated anytime the system updates. The values of
the state probabilities `p` and quantities `q` is given in the same order
that values `u` are given and must be specified after `u` is specified. The
value `Z` is the normalization factor for the probabilities when `tau != 0`.
When `tau == 0`, `Z` is a count of the states with non-zero probabilities.

Two types of `device` properties can be updated by a system model based on the
state probability `p`:

* `enumeration`: The specified property is assigned the state index number in `u`.

* `double`: The specified property is assigned the value of the quantity `q`.

# Example

The following example creates two devices with two state variables `x` and
`s`.  The system model is given activity `tau=1.0`, and two possible states 0
and 1 with values `0.0` and `1.0`, respectively.  The first device's state
variable `x` is updated based the value of the state chosen, and the second
device's state variable `s` is chosen based on the index of the state
chosen.

~~~
class device
{
    double x;
    enumeration {OFF=0,ON=1} s;
}
object device
{
    name "device_1";
}
object device
{
    name "device_2";
}

module behavior;
object system
{
    tau 1.0;
    u 0.0,1.0;
    device "device_1.s,device_2.s"
}
~~~

# See also

* [[/Module/Behavior]]
