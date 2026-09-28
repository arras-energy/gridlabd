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

```c
module NAME;
```

The module load directive is used to load a GridLAB-D or Python modules into
the solver framework. Modules provide classes and event handlers.

If the module name is a Python module, it will be loaded in the core
environment, which automatically imports the `gldcore` module. 

## Object

```c
object [MODULE.]CLASS[:..COUNT|:FIRST..LAST]
{
  PROPERTY_1 VALUE_1;
  PROPERTY_2 VALUE_2;
  ...
  PROPERTY_N VALUE_N;
  [NESTED_OBJECTS ...]
}
```

The object directive is used to instantiate one or more objects in a GridLAB-D
model.

To instantiate a single object:

```c
object [MODULE.]CLASS
{
  ...
}
```

To instantiate multiple objects:

```c
object [MODULE.]CLASS[:..COUNT]
{
  ...
}
```

To instantiate multiple objects with a specified range of object ids:

```c
object [MODULE.]CLASS[:FIRST..LAST]
{
  ...
}
```

To instantiate an object with nested objects:

```c
object [MODULE.]CLASS
{
  ...
  object [MODULE.]CLASS
  {
    ...
  };
}
```

### Caveat

When nesting objects, it is often necessary to refer to properties of the
parent object. The backtic syntax is used to embed properties in strings,
e.g.,

```c
class test 
{
  char32 output;
}

object test
{
  object test 
  {
    name "my_test";
    output `id_{id}`; 
  };
}
```

To run this example, use the following commands:

```
shell% gridlabd /tmp/test.glm -o /tmp/test.json 
shell% gridlabd json-get objects my_test output </tmp/test.json
id_1
```

## Schedule

```c
schedule <schedule-name> 
{
    [normal;]
    [weighted;]
    [absolute;]
    [nonzero;]
    [positive;]
    [boolean;]
    [interpolate;]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [// <GLM comment>]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [# <schedule comment>]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [[/<minutes> <hours> <days> <months> <weekdays> <value>;] <...>]
    <...>
}
```

-or-

```c
schedule <schedule-name> 
{
    [normal;]
    [weighted;]
    [absolute;]
    [nonzero;]
    [positive;]
    [boolean;]
    [interpolate;]
    <blockname> {
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [// <GLM comment>]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [# <schedule comment>]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [[/<minutes> <hours> <days> <months> <weekdays> <value>;] <...>]
    <...>
}
```

Schedules are used to defined a value that changes over time in a pre-defined
manner. All times in schedules are considered in local time, including
timezone offset and daylight-saving/summer time offsets. Schedule are used by
loadshapes properties and by transforms to apply the current value to other
property types.

The general form of a simple schedule entry

```c
schedule my_schedule 
{
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [// <GLM comment>]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [# <schedule comment>]
    <minutes> <hours> <days> <months> <weekdays> <value>[;] [[/<minutes> <hours> <days> <months> <weekdays> <value>;] <...>]
}
```

The schedule directive can contain either a simple schedule, such as

```x
schedule officehours 
{
    * 8-17 * * 1-5 # M-F 8a to 5p
}
```

or a complex schedule with multiple blocks, such as

```c
schedule officehours 
{
    weekdays {
        * 8-16 * * 1-5 # Monday through Friday, 8am to 5pm
    }
    weekends {
        * 9-11,13-15 * * 6 # Saturdays, 9am-noon and 1pm to 4pm
    }
}
```

If you want to provide values for each time interval, they can be listed after
the time specification, such as

```c
schedule tou_price 
{
    * 21-8 * * 1-5 35 # weekdays 9pm-9am, $35
    * 9-20 * * 1-5 135 # weekdays 9am-9pm, $135
    * * * * 6-0 35 # weekends, $35
}
```

Omitted values on schedule items take on the default value of 1. Omitted times
in the schedule take on the default value of 0.

### Options

#### Normalization

Some schedules need to be normalized before they are used, depending on the
application (e.g., loadshapes). When normalization takes place it is done
separately over each block. The (optionally weighted) sum of the values given
within the block is the normalization coefficient --- each value in the block
is divided by the sum of all the values in the block. Some applications may
need the signed sum and others may use the sum of the absolute values.

When weighting is used it is based on the fraction of minutes over which the
value applies with respect to the total minutes over which the block applies.
Only minutes that are explicitly listed in the block are count---omitted
times (which are associated with the value 0.0) are ignored. If you wish to
have the value 0 counted in the weighting, you must include the times for
which it applies as well.

Normalization is controlled using the following options

* `normal` : enables normalization so that all values in each block are
  divided by the sum of the values in the block.

* `absolute` : normalization sums uses absolute values instead signed values.
  Its inclusion implies normal.

* `weighted` : normalization sums uses time-weighted values instead of simple
  values. Its inclusion implies normal.

Normalization options should be provided in-line, such as

```c
schedule demand 
{
    weighted;
    * 21-8 * * 1-5 1.2 # weekdays 9pm-9am, weeknights
    * 9-20 * * 1-5 1.5 # weekdays 9am-9pm, weekdays
    * * * * 6-0    0.8 # weekends, holidays
}
```

which enables normalization using time-weighted values.

#### Nonzero

The nonzero flag can be used to ensure that the schedule does not contain any
undefined or zero values:

```c
schedule demand 
{
    nonzero;
    * 21-8 * * 1-5 1.2 # weekdays 9pm-9am, weeknights
    * 9-20 * * 1-5 1.5 # weekdays 9am-9pm, weekdays
    * * * * 6-0    0.8 # weekends, holidays
}
```

#### Positive

The positive flag can be used to ensure that the schedule does not contain any
negative values:

```c
schedule demand 
{
    positive;
    * 21-8 * * 1-5 1.2 # weekdays 9pm-9am, weeknights
    * 9-20 * * 1-5 1.5 # weekdays 9am-9pm, weekdays
    * * * * 6-0    0.8 # weekends, holidays
}
```

#### Boolean

The boolean flag can be used to ensure that the schedule contains on 0 or 1
values:

```c
schedule demand 
{
    boolean;
    * 21-8 * * 1-5 1 # weekdays 9pm-9am, weeknights
    * 9-20 * * 1-5 1 # weekdays 9am-9pm, weekdays
    * * * * 6-0    0 # weekends, holidays
}
```

#### Absolute

The absolute flag can be used to ensure that the schedule normalization uses
only positive magnitudes:

```c
schedule demand 
{
    absolute;
    * 21-8 * * 1-5 1.2 # weekdays 9pm-9am, weeknights
    * 9-20 * * 1-5 1.5 # weekdays 9am-9pm, weekdays
    * * * * 6-0    0.8 # weekends, holidays
}
```

#### Interpolation

The interpolate flag can be used to ensure that values used are interpolated
linearly for times between schedule changes. Warning: use of this option may
cause answers to vary depending on when objects update.

### Caveats

There may be no more than 4 blocks, and each block may not contain more than
63 distinct non-zero values. Although you may have more than 64 schedule
entries in a block, the number of distinct values cannot exceed 64, and zero
is always a value. If you have defined more than 63 distinct values, you can
either limit the resolution over the dynamic range, or you can use a orphaned
player (i.e., having no parent) as a source instead.

There are some notable differences from the cron syntax:

1. The alternate use of day and weekday is not supported. If both day and
weekday are not *, they are considered as day AND weekday rather than OR.

2. The step by syntax (using /) is not supported.

3. The special keywords (e.g., \@hourly, \@daily) are not supported.

4. The weekday 7 refers to holidays, which can occur any day of the week.
Holidays are not supported yet, but will be someday.

Because all times are considered in local time, there is a possibility that
scheduled changes during on the daylight-savings/summer time (DST) shifts
could result in a missing or duplicate value. For example, scheduling an
event at 2am the night DST ends may result in a duplicate value. The solution
is to schedule the event either before or after am so the ambiguity is
resolved internally as appropriate. Similarly, scheduling an event at 2am the
night DST starts could result in a gap in the schedule, a problem also
resolved by scheduling the event either before or after 2am so the gap is
automatically filled by the schedule compiler.

## Script

```c
script command;
script on_create command;
script on_init command;
script on_precommit command;
script on_presync command;
script on_sync command;
script on_postsync command;
script on_commit command;
script on_term command;
script export global-name;
```

### Description

The script directives cause external commands to be executed. The simulation
will wait for the command to exit. If the exit code is non-zero, the
simulation will immediately terminate with the exit code returned by the
script.

Loader scripts (those without event specifications) are loaded one at a time
in the order in which they are encountered by the loader.

Event scripts may be run in parallel if the threadcount is greater than 1.

`export`: The variable listed is exported to the shell's environment before
script are executed.

Note: The syntax for accessing a variable is dependent on the shell being used to interpret the script commands. For example, DOS uses the %name% syntax whereas bash uses the $name syntax.

`on_create`: The script is executed after all objects have been created and
before the first object is initialized.

`on_init`: The script is executed after all objects have been initialized and
before the first sync event.

`on_[pre]commit`: The script is executed before/after committing a clock
step.

`on_[pre|post]sync`: The script is executed after the specified clock
synchronization pass has been completed.

`on_term`: The script is executed when the simulation terminates.

### Caveat

* Platform independence

  - In the current implementation, scripts are interpreted by the platform's native shell command processor (e.g., DOS for MS Windows, bash for linux and Mac). This means GLM files that use scripts are not normally portable from one platform to another.

  - On most platforms you can specify the shell to use by preceding the command with the name of the shell, e.g. script python my_script.py.

  - Provided you include the shell command in the your PATH environment. If platform independent scripts are desired, care should be take to only use those shell features that are platform independent. See the shell's documentation for details.

* Asynchronous calls

  - On MS Windows platform the DOS shell interprets the start command as a request for asynchronous execution of the script. On Linux/Mac platforms, a trailing & causes asynchronous execution of the script. If a script request is repeated before the previous copy if done (e.g., on_sync), this can result in many copies of the script running concurrently and the system becoming bogged down with multiple copies of the same process.

* Variable expansion

  - Variable names are interpreted when the script command is parsed by the GLM rather than when it is executed. It is currently not possible to update the value of a variable when the script is executed. As a result, the following directive will not work as expected script on_sync echo ${clock} because the value of the clock is interpreted when the directive is encountered (when clock contains the start time) and not when the script is executed. You must use the export option to export variables to scripts. The correct syntax for the above example is
```
    script export clock;
    script on_sync echo $clock; // linux/mac variable expansion syntax
```

# General

## Collection

<property><comparison><value> [{and|AND|;} ... ] 
Description
Several objects use collections as a property to help find objects that satisfy certain criteria. Collections are typically built at initialization, although that can be run at any during a simulation if needed.

A collection is specified as string with one or more filtering elements. For example,

  class=house
would collect all the objects that are of class house.

Only properties that are invariant during a simulation may be used in a collection. The following properties are supported:

id
class
isa
module
groupid
rank
parent
insvc
name
latitude
longitude
clock
insvc
outsvc
flags
The following operators are supported:

AND (can also be written as "and" or ";")
Search criteria
Object searches are usually expressed using a search criteria, such as

```c
object class 
{ 
  group "<property> <comparison> <value>";  
  // ..  
}
```

where class is the class of object that uses the group property (e.g., collector, histogram), property is the object property name to match against (e.g., name, class, parent), comparison is the comparison operator (e.g., ==, <, !~), and value the value to match against.

Operators
!= : Not equal, e.g., property!=value
<= : Less than or equal, e.g., property<=value
>= : Greater than or equal, e.g., property>=value
!~ : Not like, e.g., property!pattern
= : Equal
Caveats
The OR operator is not supported at this time.

Multiple search criteria can be indicated using and/or as appropriate.
Parenthetical operators are not supported.

The implementation of the and and or operators is incomplete and not
mathematically correct. Any logical statement joined with an and will remove
all objects not identified with that operation from the working set. Any
logical statement joined with an or will add all objects that match that
operation to the working set. There is no sense of operator precedence, and
operators are processed from left to right.

Date and time values must be fully qualified absolute date/time stamps using
the appropriate timezone. Relative time can also be given using s, m, h, d,
or w suffixes as desired, e.g., 1800s to indicate 30 minutes.



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