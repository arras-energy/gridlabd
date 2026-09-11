r"""GridLAB-D GLM Language Syntax

# Directives

Directives are undecorated tokens in the GLM file that introduce
a line or block of modeling code.

| Directive  | Introduces |
| ---------- | :--------: |
| [`class`](#class) | block
| [`clock`](#clock) | block
| [`dump`](#dump) | line
| [`filter`](#filter) | line
| [`global`](#global) | line
| [`loader`](#loader) | line
| [`modify`](#modify) | line
| [`module`](#module) | line or block
| [`object`](#object) | block
| [`schedule`](#schedule) | block
| [`script`](#script) | line

## Class

```c
class NAME
{
    TYPE NAME; 
    TYPE NAME[UNITS];
    TYPE SPECIFICATION NAME; 
    EVENT "SCRIPT";
    EVENT "python:MODULE.NAME";
}
```

The `class` directive define a new runtime class.

Types can be verified or added to a class using the `TYPE ...` declaration.
If the type is already defined, then the declaration can serve as a
verification of the previous declaration. If the declarations differs, the
loader will fail. If the type is not already defined, the declaration will
add a new property to the class.

Event handlers can be defined in the same manner as for individual objects.
When an event handler is defined for a class, then all objects of that class
will implement the event handler. If an object subsequently defines its own
event handler, the new event handler will be only be used for that object,
and will be called in place of the class's event handler unless the object's
event handler returns `0`, which indicates that a passthru to the class's
event handler is required.

### Types

The following types are recognized.

| Type | Description |
| ---- | ----------- |
| `void` | Empty property |
| `bool` | Boolean property, e.g., `TRUE` or `FALSE` |
| `int16` | 16-bit integer |
| `int32` | 32-bit integer |
| `int64` | 64-bit integer |
| `double` | floating point value with optional UNITS |
| `complex` | complex value with optional UNITS |
| `string` | string of text |
| `python` | Python data |
| `enumeration` | enumeration of specified value |
| `set` | set of specified values |

### Specifications

When defining an enumeration or a set, a specification must be included. The
syntax for a specification takes the form

```{KEY=VALUE[,...]}```

where `KEY` is a unique tag within the scope of the property and `VALUE` is a
non-negative integer. The value `0` is reserved for the default value of the
property.

### See also

- [Object Events](#events)

## Clock

```c
clock
{
    timezone "SPECIFICATION";
    starttime "YYYY-MM-DD HH:MM:SS[ ZZZ]";
    stoptime "YYYY-MM-DD HH:MM:SS[ ZZZ]";
}
```

The `clock` directive specifies how the internal clock will operate while a
simulation runs. The internal clock of a simulation runs separately from the
host operating system clock, including separate handling of the timezone and
daylight savings time.

- `timezone`: the `timezone` property sets the time zone for the simulation.
  The time zone may be specified either as a ISO timezone, e.g.,
  `"PST+8PDT"`, or a locale, e.g., `"US/CA/San Francisco"`. If the time zone
  is not specified the simulation will use UTC.

- `starttime`: the starttime property specifies when the simulation start. If
  no time zone is specified, the current time zone is used if it has been
  specified. Otherwise UTC is assumed. If no start time is specified, the
  current wall clock time is used. Note, ISO8601 is supported.

- `stoptime`: the stoptime property specifies when the simulation stops. If no
  time zone is specified, the current time zone is used if it has been
  specified. Otherwise UTC is assumed. If no stop time is specified, NEVER is
  used, which means that the simulation will run until a steady state is
  achieved, if ever. Note, ISO8601 is supported.

## Dump

```dump INTERVAL FILENAME;```

The `dump` directive causes the dump file filename to be generated at the
interval times.

If the filename starts with a dash, then the output is sent to stdout in GLM
format. Adding the extension after the dash causes the specified format to
use generated (i.e., `glm` or `json`).

## Filter

```filter NAME(DOMAIN[,TIMESTEP[,TIMESKEW[,OPTION=VALUE[,...]]]]) = POLYNOMIAL/POLYNOMIAL;```

The filter directive defines a filter that can be used to connect a signal
source property to a output signal property.

Filters may be used to output values to an object property of type double.
Outputs are summed so that multiple filter may output to a single property,
e.g.,

```c
object example
{
  output1 filter11(input1);
  output1 filter21(input2);
  output2 filter12(input1);
  output2 filter22(input2);
}
```

represents a MIMO system with two inputs going to two outputs through 4
different filters with outputs summed.

Filter specifications include the following

- `NAME`: Any unique alphabetic name may be used.

- `DOMAIN`: Only discrete-time $z$-domain filters are supported.

- `TIMESTEP`: Specifies the discrete-time filter timestep

- `TIMESKEW`: Specifies the time-shift for the discrete-time sampling.

- `POLYNOMIAL`: The numerator and denominator are specified as a polynomial of the form 
$ a_n z^n + a_{n−1} z^{n-1} + \cdots + a_2 z^2 + a_1 z + a_0$
, e.g.,  `an z^n + ... + a1 z + a0`. The order of the numerator must be less
  than or equal to the order of the denominator.

For example

```c
filter integrate(z,1) = z/(z-1);
class test
{
	double value;
}
object test {
  name "source";
  value 0.0;
}
object test {
  name "destination";
  value integrate(source.value);
}
```

integrates `source.value` into `destination.value`.

The following options may be specified

- `resolution=N`: specifies the number of bits of resolution in the output.

- `minimum=DOUBLE`: specifies the minimum value that may be output

- `maximum=DOUBLE`: specifies the maximum value that may be output

For example

```filter delay(z,5min,10s,resolution=8,minimum=-2.5,maximum=2.5) = 1/z;```

creates a filter with 8 bits of resolution (256 values) over a dynamic range
of 5.0 that updates every 5 minutes with a 10 second delay.

## Global

`global TYPE NAME[UNIT] VALUE [UNIT];`

Defines a new global variable of the specified `TYPE` and `NAME`. If the type
is `double` or `complex` the optional `UNIT` may be specified. The variable
is initialized to `VALUE` with an optional `UNIT`. If the value's unit
differs from the variable's unit the conversion is performed automatically.

The following example defines a complex global variable named my_value with
units kV and defines it as having magnitude 12 and angle 1 deg.

`global complex my_value[kV] 12+1d kV;`

## Modify

```modify NAME.PROPERTY VALUE;```

The modify directive changes the values of properties in objects that have
already been loaded.

The following example modifies the value the property

```c
class test 
{
	double output;
}

object test
{
	name "my_test";
	output "1.0";
}

modify my_test.output 2.0;
```

To run this example, do the following:

```
gridlabd /tmp/test.glm -o /tmp/test.json
gridlabd json-get objects my_test output </tmp/test.json
```

which should output `2`.

## Module

TODO

## Object

TODO

## Schedule

TODO

## Script

TODO

# General

TODO

## Collection

TODO

## Expansion

TODO

## Functional

TODO

## Inherit

TODO

## Json

TODO

## Random

TODO

## Range

TODO

# Globals

TODO

## Expansion

TODO

## Filename

TODO

## Filepath

TODO

## Filetype

TODO

## Find

TODO

## Geocode

TODO

## Now

TODO

## Python

TODO

## Random

TODO

## Range

TODO

## Shell

TODO

## Tmpfile

TODO

# Macros

TODO

## Begin

TODO

## Curl

TODO

## Debug

TODO

## Define

TODO

## Error

TODO

## Exec

TODO

## For

TODO

## Gridlabd

TODO

## If

TODO

## Ifdef

TODO

## Ifexist

TODO

## Ifmissing

TODO

## Ifndef

TODO

## Include

TODO

## Input

TODO

## Insert

TODO

## On exit

TODO

## Option

TODO

## Output

TODO

## Print

TODO

## Save

TODO

## Set

TODO

## Setenv

TODO

## Sleep

TODO

## Start

TODO

## Subcommand

TODO

## System

TODO

## Verbose

TODO

## Version

TODO

## Wait

TODO

## Warning

TODO

## Wget

TODO

## Write

# Objects

TODO 

## Events

TODO

# Properties

TODO

## Python

TODO

## Randomvar

TODO

## String

TODO

## Timestamp

TODO
"""