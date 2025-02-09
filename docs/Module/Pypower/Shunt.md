[[/Module/Pypower/Shunt.md]] -- Shunt capacitor/reactor

# Synopsis

~~~
class shunt {
    enumeration {DISCRETE_V=1, FIXED=0} control_mode; // shunt control mode
    enumeration {ONLINE=1, OFFLINE=0} status; // shunt status
    double voltage_high[pu]; // controlled voltage upper limit
    double voltage_low[pu]; // controlled voltage lower limit
    object remote_bus; // remote bus name
    double admittance[MVAr]; // shunt admittance at unity voltage
    int32 steps_1; // numbers of steps in control block 1
    double admittance_1[MVAr]; // control block 1 shunt admittance step at unity voltage
}
~~~

# Description

Shunt objects are used to control voltage of its `parent` bus. Shunt capacitors can raise voltage and shunt reactors can lower voltage. Shunt devices can be controlled by monitoring voltage on a remote bus and stepping the reactive power injections up or down according to the voltage control limits.

Each control block has a number of steps for the admittance steps allowed. Note: at this time, only 1 control block is supported.

# Properties

The following properties determine how a `shunt` device operates.

## `enumeration control_mode`

Determines the shunt device control mode.

### `FIXED`

The shunt device is fixed and does not change the shunt admittance of the parent bus.

### `DISCRETE_V`

The shunt device varies the shunt admittances of the `parent` bus according to the voltage control limits of the `remote_bus`, if specified. If the `remote_bus` is not specified then the `parent` bus is used as the control input.

## `enumeration status`

Shunt device status.

### `ONLINE`

The shunt device is active and will change the admittance of the `parent` bus.

### `OFFLINE`

The shunt device is inactive and will not change the admittance of the `parent` bus.

## `double voltage_high[pu]`

The upper voltage limit at which the shunt device's voltage lowering strategy will be engaged.

## `double voltage_low[pu]`

The lower voltage limit at which the shunt device's voltage raising strategy will be engaged.

## `object remote_bus`

The name of the remote bus from which voltage input is measured. If not specified, the `parent` bus is used as the voltage input.

## `double admittance[MVAr]`

The shunt admittance used when the shunt device is engaged, specified at unity voltage.

## `int32 steps_1`

The number of admittance steps in control block 1.


## `double admittance_1[MVAr]`

The admittance step of control block 1, specified at unity voltage.

# Examples

The following implements a shunt capacitor with 5 steps of 200 MVAr admittance on a test swing bus in `pypower`.

~~~
module pypower;
object pypower.bus 
{
    name "test_bus"; 
    baseKV 345.0000 kV;
    type REF; 
}
object shunt { 
    name "test_shunt";
    parent "test_bus";
    control_mode DISCRETE_V;
    status ONLINE;
    voltage_high 1.5 pu;
    voltage_low 0.5 pu;
    admittance 200.0 MVAr;
    steps_1 5;
    admittance_1 200.0 MVAr;
}
~~~

# See Also

* [[/Module/Pypower.md]]
