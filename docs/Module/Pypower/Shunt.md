[[/Module/Pypower/Shunt.md]] -- Voltage-controlled shunt device

# Synopsis

~~~
module pypower
{
    double minimum_voltage_deadband[pu]; 
}
class shunt {
    enumeration {CONTINUOUS=2, DISCRETE=1, FIXED=0} control_mode; // shunt control mode
    enumeration {ONLINE=1, OFFLINE=0} status; // shunt status
    enumeration {ANGLE=1, MAGNITUDE=0} input; // voltage input
    enumeration {REAL=1, REACTIVE=0} output; // shunt output
    double voltage_high[pu]; // controlled voltage upper limit
    double voltage_low[pu]; // controlled voltage lower limit
    object remote_bus; // remote bus name
    double admittance[MW]; // shunt admittance at unity voltage
    int32 steps_1; // numbers of steps in control block 1
    double admittance_1[MW]; // control block 1 shunt admittance step at unity voltage
    double dwell_time[s]; // control lockout time before next control action
}
~~~

# Description

Shunt objects are used to manage the voltage of its `parent` bus. A shunt device
can be a capacitor or synchronous condense, depending on the values of the properties describing the device. 

Shunt devices' `control_mode` is either `FIXED`, `DISCRETE` for capacitor, or
`CONTINOUS` for synchronous condenser. Shunts are controlled by monitoring
voltage magnitude on the `parent` bus (or the remote bus if `remote_bus` is
specified). For example, capacitors are controlled over the ranges of
`steps_1` if non-zero, with each step incrementing the capacitor by
`admittance_1` MW, allowing `admittance` to have values from 0 to
`step_1*admittance_1`, inclusive. Synchronous condensers have a `step_1` of
zero, and the `admittance` can have continuous values from `-admittance_1` to
`+admittance_1`, inclusive.

The `minimum_voltage_deadband` specifies the minimum separation between the
`voltage_low` and `voltage_high` that will result in an error.

The following table is a guide to some typical shunt device properties

| Device | Property | Value | Remarks
| ------ | -------- | ----- | -------
| Capacitor | `control_mode` | `DISCRETE` | control from `0` to `step_1 x admittance_1`
|           | `input` | `MAGNITUDE` | measure voltage magnitude
|           | `output` | `REACTIVE` | convert real power to reactive power
|           | `voltage_low` | e.g., `0.95` | voltage below which to add reactive power
|           | `voltage_high` | e.g., `1.05` | voltage above which to reduce reactive power
|           | `step_1` | e.g., `10` | number of discrete control steps
|           | `admittance_1` | e.g., `0.1 MW` | susceptance change per control step
| Condenser | `control_mode` | `CONTINUOUS` | control from `-admittance_1` to `+admittance_1`
|           | `input` | `MAGNITUDE` | measure voltage magnitude
|           | `output` | `REACTIVE` | convert real power to reactive power
|           | `voltage_low` | e.g., `0.95` | voltage below which to add reactive power
|           | `voltage_high` | e.g., `1.05` | voltage above which to reduce reactive power
|           | `admittance_1` | e.g., `1 MW` | susceptance limit (positive or negative)

# Properties

The following properties determine how a `shunt` device operates.

## `enumeration control_mode`

Determines the shunt device control mode.

### `FIXED`

The shunt device is fixed and does not change the shunt admittance of the
parent bus.

### `DISCRETE`

The shunt device `admittance` varies the admittance `Gs` or susceptance `Bs`
of the `parent` bus according to the value of `output` in response to the
voltage inputs of the `remote_bus`, if specified. If the `remote_bus`
is not specified then the `parent` bus is used as the control input.

### `CONTINOUS`

The shunt device `admittance` varies the admittance `Gs` or susceptance `Bs`
of the `parent` bus according to the value of `output` in response to the
voltage inputs of the `remote_bus`, if specified. If the `remote_bus`
is not specified then the `parent` bus is used as the control input.

## `enumeration status`

Shunt device status.

### `ONLINE`

The shunt device is active and will change the admittance of the `parent`
bus.

### `OFFLINE`

The shunt device is inactive and will not change the admittance of the
`parent` bus.

## `input`

The `input` properties determine whether the input voltage is the angle or magnitude measured at the bus.

### `ANGLE`

The input voltage angle is measured and compared to `voltage_high` and `voltage_low`.

### `MAGNITUDE`

The input voltage magnitude is measured and compared to `voltage_high` and `voltage_low`.

## `output`

### `REAL`

The output consumed real power at the bus.

### `REACTIVE`

The output converts real power to reactive power at the bus.

## `double voltage_high[pu]`

The upper voltage limit at which the shunt device's voltage lowering strategy
will be engaged.

## `double voltage_low[pu]`

The lower voltage limit at which the shunt device's voltage raising strategy
will be engaged.

## `object remote_bus`

The name of the remote bus from which voltage input is measured. If not
specified, the `parent` bus is used as the voltage input.

## `double admittance[MVAr]`

The shunt admittance used when the shunt device is engaged, specified at unity
voltage.

## `int32 steps_1`

The number of admittance steps in control block 1.

## `double admittance_1[MVAr]`

The admittance step of control block 1, specified at unity voltage.

## `dwell_time[s]`

The control lockout time before another control can be taken.

# Examples

The following implements a shunt capacitor with 5 steps of 200 MVAr admittance
on a test swing bus in `pypower`.

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
    control_mode DISCRETE;
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
