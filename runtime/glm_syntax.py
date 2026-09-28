r"""GridLAB-D GLM Language Syntax

# **Directives**

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

----

## Class

```
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

----

## Clock

```
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

----

## Dump

```dump INTERVAL FILENAME;```

The `dump` directive causes the dump file filename to be generated at the
interval times.

If the filename starts with a dash, then the output is sent to stdout in GLM
format. Adding the extension after the dash causes the specified format to
use generated (i.e., `glm` or `json`).

----

## Filter

```filter NAME(DOMAIN[,TIMESTEP[,TIMESKEW[,OPTION=VALUE[,...]]]]) = POLYNOMIAL/POLYNOMIAL;```

The filter directive defines a filter that can be used to connect a signal
source property to a output signal property.

Filters may be used to output values to an object property of type double.
Outputs are summed so that multiple filter may output to a single property,
e.g.,

```
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

```
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

----

## Global

`global TYPE NAME[UNIT] VALUE [UNIT];`

Defines a new global variable of the specified `TYPE` and `NAME`. If the type
is `double` or `complex` the optional `UNIT` may be specified. The variable
is initialized to `VALUE` with an optional `UNIT`. If the value's unit
differs from the variable's unit the conversion is performed automatically.

The following example defines a complex global variable named my_value with
units kV and defines it as having magnitude 12 and angle 1 deg.

`global complex my_value[kV] 12+1d kV;`

----

## Modify

```modify NAME.PROPERTY VALUE;```

The modify directive changes the values of properties in objects that have
already been loaded.

The following example modifies the value the property

```
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

----

## Module

```
module NAME;
```

The module load directive is used to load a GridLAB-D or Python modules into
the solver framework. Modules provide classes and event handlers.

If the module name is a Python module, it will be loaded in the core
environment, which automatically imports the `gldcore` module. 

----

## Object

```
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

```
object [MODULE.]CLASS
{
  ...
}
```

To instantiate multiple objects:

```
object [MODULE.]CLASS[:..COUNT]
{
  ...
}
```

To instantiate multiple objects with a specified range of object ids:

```
object [MODULE.]CLASS[:FIRST..LAST]
{
  ...
}
```

To instantiate an object with nested objects:

```
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

```
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

----

## Schedule

```
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

```
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

```
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

```
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

```
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

```
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

```
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

```
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

```
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

```
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

----

## Script

```
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

----

# **General**

----

## Collections

```
<property><comparison><value> [{and|AND|;} ... ]
```

Several objects use collections as a property to help find objects that
satisfy certain criteria. Collections are typically built at initialization,
although that can be run at any during a simulation if needed.

A collection is specified as string with one or more filtering elements. For
example,

```
class=house
```

would collect all the objects that are of class house.

Only properties that are invariant during a simulation may be used in a
collection. The following properties are supported:

- `id`

- `class`

- `isa`

- `module`

- `groupid`

- `rank`

- `parent`

- `insvc`

- `name`

- `latitude`

- `longitude`

- `clock`

- `insvc`

- `outsvc`

- `flags`

The following operators are supported:

- `AND` (can also be written as `and` or `;`)

### Search criteria

Object searches are usually expressed using a search criteria, such as

```
object class 
{ 
  group "<property> <comparison> <value>";  
  // ..  
}
```

where class is the class of object that uses the group property (e.g.,
`collector` or `histogram` in the `tape` module), property is the object
property name to match against (e.g., `name`, `class`, `parent`), comparison
is the comparison operator (e.g., `==`, `<`, `!~`), and value the value to
match against.

### Operators

- `!=` : Not equal, e.g., property!=value

- `<=` : Less than or equal, e.g., property<=value

- `>=` : Greater than or equal, e.g., property>=value

- `!~` : Not like, e.g., property!pattern

- `=` : Equal

### Caveats

The `OR` operator is not supported at this time.

Multiple search criteria can be indicated using and/or as appropriate.
Parenthetical operators are not supported.

The implementation of the and and or operators is incomplete and not
mathematically correct. Any logical statement joined with an and will remove
all objects not identified with that operation from the working set. Any
logical statement joined with an or will add all objects that match that
operation to the working set. There is no sense of operator precedence, and
operators are processed from left to right.

Date and time values must be fully qualified absolute date/time stamps using
the appropriate timezone. Relative time can also be given using `s`, `m`,
`h`, `d`, or `w` suffixes as desired, e.g., `1800s` to indicate 30 minutes.

----

## Expansion

```
object <class>
{
  name `expression`;
}
```

Expansion variables are used in GLM code to embed context-dependent values
into property values and code. Expansion variables are always enclosed in
single curly braces, e.g., {variable}. To enable expansion variable syntax,
property values must be embedded in back-quotes

The recognized expansion variables are

- `{class}` embeds the class name

- `{cpu}` embeds the CPU id (see pstatus) that is running the code Template

- `{fileext}` embeds the file extension (no path or name)

- `{filename}` embeds the base file name (no path and no extension)

- `{filepath}` embeds the path to the file (no file name or extension)

- `{file}` embeds the full GLM file name

- `{global}` embeds the value from a global variable Template

- `{gridlabd}` embeds the path to the gridlabd installation

- `{hostaddr}` embeds the host IP address of the machine running the code Template

- `{hostname}` embeds the host name of the machine running the code Template

- `{id}` embeds the object id number

- `{masteraddr}` embeds the master server simulation host IP address Template

- `{mastername}` embeds the master server simulation host name Template

- `{masterport}` embeds the master server port number Template

- `{namespace}` embeds the namespace

- `{parent}` The name of the parent object

- `{pid}` embds the process id (see pstatus that is running the code Template

- `{port}` embeds the port number of the server (if any) Template

- `{property}` embeds the property from the current object

### Example

```
module residential;
object house:..5 
{
  name `house_{id}`;
}
```

----

## Functional

```
random.<distribution>(<parameters>)
```

Functionals are used to generate initial values. For details on the supported
distributions, see Random Values.

### Example

```
class example
{
    double x;
}
object example 
{
    x random.uniform(0,100);
}
```

----

## Inherit

```
object <class>
{
    <property-name> inherit;
    <property_name> @<object-name>;
}
```

The inherit property value causes the value to be copied from the parent
object. This requires that the parent already be defined. The alternative
syntax `@<name>` inherits the property value from the named object.

### Example

This example copies the value of `x` from object `test1` into object `test2`:

```
class test
{
    double x;
}
object test
{
    name test1;
    x 1.23;
}
object test
{
    name test2;
    x @test1;
}
```

----

## Json

```
object class 
{
  property {tag1:value1; tag2:value2; ...; tagN:valueN}; // DEPRECATED
  property {"tag1":"value1", "tag2":"value2", ..., "tagN":"valueN"};
}
```

Properties that have parts may be set or updated using JSON-formatted data.

### Example

The following examples set the property `z` to the value `-i`:

```
class example 
{
  complex z;
}
object example 
{
  z "0-1i";
}
object example 
{
  z {real:0.0; imag:-1.0};
}
object example 
{
  z {mag:1.0; ang:180;};
}
object example 
{
  z {mag:1.0; arg:3.1415926;};
}
object example 
{
  z {mag:-1.0; ang:0};
}
```

----

## Random

```
degenerate(<value>)
uniform(<min>,<max>)
normal(<mean>,<stdev>)
bernoulli(<probability>)
sampled(<N>,<sample_1>,<sample_2>,...,<sample_N>)
pareto(<base>,<gamma>)
lognormal(<geometric-mu>,<geometric-sigma>)
exponential(<lambda>)
beta(<alpha>,<beta>)
gamma(<alpha>,<beta>)
weibull(<l>,<k>)
rayleigh(<s>)
triangle(<min>,<max>)
triangle_asy(<min>,<max>,<center>)
```

Random variables are generated using one of the following distributions.

### `degenerate`

```
degenerate(a)
```

The PDF is $\phi(x;a) = \left\\{ 1 : x = a ; 0 : x \ne a \right.$

### `uniform`

```
uniform(a,b)
```

The PDF is $\phi(x;a,b) = \left\\{ \frac{1}{b-a} : a \le x < b ; 0 : x < a ; 0 : x \ge b \right.$

### `normal`

```
normal(mu,sigma)
```

The PDF is $\phi(x;\mu,\sigma) = \frac{1}{\sqrt{2\pi}\sigma} e^{\frac{(x-\mu)^2}{2\sigma^2}}$.

The value is generated using the Box-Muller method.

### `bernoulli`

```
bernoulli(p)
```

The PDF is $\phi(x;p) = \left\\{ 1 : x \ge p ; 0 : x < p \right.$.

### `sampled`

```
sampled(N,a_1,a_2,...,a_N)
```

The PDF is $\phi(x;a_1,a_2,\cdots,a_N) = \left\\{ 1/N : x = a_1 ; 1/N : x = a_2 ; \cdots ; 1/N : x = a_N \right. $.

### `pareto`

```
pareto(m,k)
```

The PDF is $\phi(x;k) = \left\\{ k \frac{m^k}{x^{k+1}} : m \le x ; 0 : x < m \right.$.

### `lognormal`

```
lognormal(mu,sigma)
```

The PDF is $\phi(x) = \left\\{ \frac{1}{\sqrt{2\pi}x\sigma} e^{\frac{(\ln x-\mu)^2}{2\sigma^2}} : x > 0 ; 0 : x \le 0 \right.$.

### `exponential`

```
exponential(lambda)
```

The PDF is $\phi(x) = \left\\{ \begin{array}{ll} \lambda e^{\lambda x} & x\ge0 \\\\ 0 & x\lt0 \end{array} \right.$.

### `beta`

```
beta(alpha,beta)
```

The PDF is $\phi(x;\alpha,\beta) = \frac{\Gamma(\alpha+\beta)}{\Gamma(\alpha)\Gamma(\beta)}x^{(\alpha-1)}(1-x)^{(\beta-1)}$.

### `gamma`

```
gamma(alpha,beta)
```

The PDF is $\phi(x;\alpha,\beta) = \frac{1}{\Gamma(\alpha)\beta^\alpha}x^{(\alpha-1)}e^{-x/\beta}$.

### `weibull`

```
weibull(l,k)
```

The PDF is $\phi(x;k,\lambda) = \frac{k}{\lambda} \left(\frac{x}{\lambda}\right)^{k-1} e^{-\left(\frac{x}{\lambda}\right)^k}$.

### `rayleigh`

```
rayleigh(sigma)
```

The PDF is $\phi(x;\sigma) = \frac{xe^-\frac{x^2}{2\sigma^2}}{\sigma^2}$.

### `triangle`

```
triangle(a,b)
```

The PDF is $\phi(x;a,b) = \left\\{ \begin{array}{ll} \frac{4(x-a)}{(b-a)^2} & a \lt x \le (a+b)/2 \\\\ \frac{4(b-x)}{(b-a)^2} & (a+b)/2 < x \le b \\\\ 0 & x \le a\ |\ x \gt b \end{array}\right.$.

----

# **Globals**

----

## Expansion

```
${name=value}
${name:-value}
${name:=value}
${name:+value}
${name:offset}
${name:offset:length}
${name/pattern/value}
${name//pattern/value}
${++value}
${--value}
${value++}
${value--}
${[~]name+[~]value}
${[~]name-[~]value}
${[~]name/[~]value}
${[~]name*[~]value}
${[~]name%[~]value}
${[~]name&[~]value}
${[~]name|[~]value}
${[~]name^[~]value}
${name+=value}
${name-=value}
${name/=value}
${name*=value}
${name%=value}
${name%&[~]value}
${name%|[~]value}
${name%^[~]value}
${name[!<=>&|~]value?yesvalue:novalue}
```

Global variable expansions perform string and integer operations on global
variable of type char1024 and int32, respectively.

### `{name=value}`

Creates a new global name using value. If the value can be interpreted as an
integer, the new global will be defined as an int32. Otherwise, the new value
is defined as a char1024. Returns the value of the new global variable.

### `{name:-value}`

Returns the value assigned to name if it is defined. If name is not defined,
returns value.

### `{name:=value}`

Sets the value of the global variable if not defined. Returns the old value if
defined or value if not defined.

### `{name:+value}`

Substitutes the value is name is defined, otherwise returns nothing.

### `{name:offset}`

Returns the value of the global name starting at the character at position offset.

### `{name:offset:length}`

Returns the value of the global name starting at the character at position
offset and stopping after length characters.

### `{name/pattern/value}`

Returns the value of the global name substituting the first occurance of the
substring pattern with value.

### `{name//pattern/value}`

Returns the value of the global name substituting every occurance of the
substring pattern with value.

### `{++name}`

Returns the value of the global integer name after incrementing it by one.

### `{--name}`

Returns the value of the global integer name after decrementing it by one.

### `{name++}`

Returns the value of the global integer name before incrementing it by one.

### `{name--}`

Returns the value of the global integer name before decrementing it by one.

### `{[~]name+[~]value}`

Adds value to the value of the global integer name. The first `~` performs a
bitwise not operation on the result. The second `~` performs a bitwise not
operation on the value.

### `{[~]name-[~]value}`

Subtracts value from the value of the global integer name. The first `~`
performs a bitwise not operation on the result. The second `~` performs a
bitwise not operation on the value.

### `{[~]name/[~]value}`

Divides the value of the global integer name by value. The first `~` performs
a bitwise not operation on the result. The second `~` performs a bitwise not
operation on the value.

### `{[~]name*[~]value}`

Multiplies the value of the global integer name by value. The first `~` performs
a bitwise not operation on the result. The second `~` performs a bitwise not
operation on the value.

### `{[~]name%[~]value}`

Uses value to perform the modulo operation on the value of the global integer
name. The first ~ performs a bitwise not operation on the result. The second
~ performs a bitwise not operation on the value.

### `{[~]name&[~]value}`

Performs the bitwise and operation of value on the value of the global integer
name. The first ~ performs a bitwise not operation on the result. The second
~ performs a bitwise not operation on the value.

### `{[~]name|[~]value}`

Performs the bitwise or operation of value on the value of the global integer
name. The first ~ performs a bitwise not operation on the result. The second
~ performs a bitwise not operation on the value.

### `{[~]name^[~]value}`

Performs the bitwise xor operation of value on the value of the global integer
name. The first ~ performs a bitwise not operation on the result. The second
~ performs a bitwise not operation on the value.

### `{name+=value}`

Increments the value of the global integer name by value and returns the
result.

### `{name-=value}`

Decrements the value of the global integer name by value and returns the result.

### `{name/=value}`

Divides the value of the global integer name by value and returns the result.

### `{name*=value}`

Multiplies the value of the global integer name by value and returns the result.

### `{name%=value}`

Performs the modulo operation on the value of the global integer name using
value and returns the result.

### `{name%&[~]value}`

Performs the bitwise and operation on the value of the global integer name
using value and returns the result.

### `{name%|[~]value}`

Performs the bitwise or operation on the value of the global integer name
using value and returns the result.

### `{name%^[~]value}`

Performs the bitwise xor operation on the value of the global integer name
using value and returns the result.

### `{name[!<=>&|~]value?yesvalue:novalue}`

Compares the global variable name to value and returns yesvalue if true and
novalue if false.

----

## Filename

```
${FILENAME string}
${FILENAME $global}
```

The name portion of a pathname variable is inserted into the GLM file.

### Example

The following example prints the name of the current model file:

```
#print ${FILENAME $modelname}
```

----

## Filepath

```
${FILEPATH string}
${FILEPATH $global}
```

The path portion of a pathname variable is inserted into the GLM file.

### Example

The following example prints the path to the current model file:

```
#print ${FILEPATH $modelname}
```

----

## Filetype

```
${FILETYPE string}
${FILETYPE $global}
```

The file type (i.e., the extension) of a pathname variable is inserted into
the GLM file.

The following example prints the extension of the current model file:

```
#print ${FILETYPE $modelname}
```

----

## Find

```
${FINDFILE criteria}
```

The objects that match the criteria are added to the list.

### Example

The following example prints the object of class test:

```
class test
{
    double x;
}
object test
{
    name my_test;
}
object test:..2
{
}
#print ${FIND class=test}
```

Running this model gives the following output:

```
/tmp/test.glm(12): my_test test:1 test:2
```

----

## Findfile

```
${FINDFILE filename}
```

The full pathname is inserted into the GLM file at the location of the global
expansion.

### Example

The following example prints the full path name of a downloaded weather file:

```
#weather get Seattle
#setenv GLPATH=${GLPATH}:${GLPATH}/weather/US
#print ${FINDFILE WA-Seattle_Seattletacoma_Intl_A.tmy3}
```

----

## Geocode

```
${GEOCODE <latitude>,<longitude>[#<resolution>]}
${GEOCODE <objname>[#<resolution>]}
${GEOCODE <geohash>[.lat|.lon]}
```

Return the geohash code corresponding to the latitude/longitude given or the
object name. This can be helpful is connecting object based on location, such
as linking an object to weather.

The default resolution is 5. The resolution corresponds to the following
distances:

```
1   2500 km
2   600 km
3   80 km
4   20 km
5   2.5 km
6   0.2 km
7   0.08 km
8   0.02 km
9   0.0025 km
10  0.0006 km
11  0.000075 km
```

The reverse conversion transfer the geohash into a latitude/longitude pair. If
the `.lat` or `.lon` spec is include, then only the corresponding value is
returned.

### Example

The following example prints the geohash codes for a position and an object:

```
class test
{
    char32 geocode;
}
object test
{
    name "test";
    latitude 37.5;
    longitude -122.2;
}
#print ${GEOCODE 37.5,-122.2#6}
#print ${GEOCODE test#6}
#print ${GEOCODE 9q9j76}
#print ${GEOCODE 9q9j76.lat}
#print ${GEOCODE 9q9j76.lon}
```

----

## Now

```
${NOW}
${NOW FORMAT}
```

If used without the FORMAT, then the format used is %Y%m%d-%H%M%S.

### Example

File `/tmp/test.glm`:

```
#print ${NOW}
#print ${NOW %m/%d/%y %H:%M}
```

Run the following:

```
gridlabd /tmp/test.glm
```

Output:

```
20231008-101445
10/08/23 10:14
```

----

## Python

```
${PYTHON <expression>}
```

The python expression is inserted into the GLM file at the location of the
global expansion.

### Example

The following example prints the python list `[1,2,3]`:

```
#print ${PYTHON [1,2,3]}
```

----

## Random

```
${RANDOM}
${RANDOM SPEC}
```

If used without the SPEC, a random uniform number between 0 and 1 is generated.

The following is permitted for SPEC:

- `N`: generate a N-bit unsigned integer where $0 \lt N \le 64$.

- `TYPE(A[,B])`: generate a random number of the specified distriction TYPE given the arguments provided. See [[/GLM/General/Random%20values.md]] for a list of distributions and their arguments.

- `last`: return the last random number generated.

If no random number has been previously generated and last is called, the value of the global randomseed is returned.

### Example

File `test.glm`:

```
#set suppress_repeat_messages=FALSE
#print Random uniform.......... ${RANDOM}
#print Random 8-bit integer... ${RANDOM 8}
#print Random 16-bit integer... ${RANDOM 16}
#print Random 32-bit integer... ${RANDOM 32}
#print Random 48-bit integer... ${RANDOM 48}
#print Random 64-bit integer... ${RANDOM 64}
#print Random normal........... ${RANDOM normal(0,1)}
#print Last number generated... ${RANDOM last}
```

Run the following:

```
gridlabd test.glm
```

Output:

```
./test.glm(2): Random uniform.......... 0.196869
./test.glm(3): Random 8-bit integer... 156
./test.glm(4): Random 16-bit integer... 238
./test.glm(5): Random 32-bit integer... 996881412
./test.glm(6): Random 48-bit integer... 5506770547858
./test.glm(7): Random 64-bit integer... 8577238717949152431
./test.glm(8): Random normal........... 1.33329
./test.glm(9): Last number generated... 1.33329
```

----

## Range

```
${RANGE[<delimiter>[<start>[,<stop>[,<step>]]]]}
```

The RANGE global generates a series of delimited values. The following
syntaxes are supported.

- `${RANGE}`

This syntax will generate the default range, which is `0 1`.

- `${RANGE<delim>}`

This syntax will generate the default range, which is `0<delim>1`.

- `${RANGE<delim><start>}`

This syntax will generate a range from `<start>` to 1 using `<delimiter>` between
the values, and incrementing by `1.0` between values.

- `${RANGE<delim><start>,<stop>}`

This syntax will generate a range from `<start>` to `<stop>` using `<delimiter>`
between the values, and incrementing by `1.0` between values.

- `${RANGE<delim><start>,<stop>,<step>}`

This syntax will generate a range from `<start>` to `<stop>` using `<delimiter>`
between the values, and incrementing by `<step>` between values.

### Example

The following GLM file generates various ranges.

`range_example.glm`:

```
#set suppress_repeat_messages=FALSE
#print ${RANGE}
#print ${RANGE,}
#print ${RANGE -1}
#print ${RANGE;1,10};
#print ${RANGE,1,10,0.5}
```

The output is as follows:

```
range_example.glm(2): 0 1
range_example.glm(3): 0,1
range_example.glm(4): -1 0 1
range_example.glm(5): 1;2;3;4;5;6;7;8;9;10;
range_example.glm(6): 1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10
```

----

## Shell

```
${SHELL <expression>}
```

The shell command output is inserted into the GLM file at the location of the
global expansion.

### Example

The following example prints the list `1 2 3`:

```
#print ${SHELL echo "1 2 3"}
```

----

## Tmpfile

```
${TMPFILE}
${TMPFILE TAG}
```

Create and access a temporary file using a tag. The file is deleted when the
GridLAB-D run is completed. The file is located in the TMPDIR or TMP or /tmp
folder, whichever is found first. The file naming convention is
`gridlabd_tmp_HOSTNAME_PID_NAME.EXT, where

- `HOSTNAME` is the name of the local host machine

- `PID` is the process ID of the current gridlabd run

- `NAME` is the tag name

- `EXT` is the tag type

If TAG is omitted, a random tag is generated. If TAG has the format EXT:NAME
these are used in constructing the file name, otherwise NAME is set to TAG.

### Example

Create the file `/tmp/test.glm`:

```
#print ${TMPFILE py:A}
#exec ls ${TMPFILE py:A}
```

Run the following command:

```
export TMP=/tmp
gridlabd /tmp/test.glm
ls /tmp/gridlabd*
```

Output:

```
/tmp/test.glm(1): /tmp/gridlabd_tmp_MacBook_Pro_2_local_10391_A.py
/tmp/gridlabd_tmp_MacBook_Pro_2_local_10391_A.py
/tmp/gridlabd-pmap-4
```

----

# **Macros**

----

## Begin

```
#begin <language>
<code>
#end
```

The `#begin` macro is used activate a new language interpreter. The new
interpreter is active until the `#end` macro is encountered.

### Built-in Languages

The following languages are currently provide through built-in support.

- `python`: The Python3 interpreter is linked to the GLM loader automatically
  when GridLAB-D is built. All the objects in the `gridlabd` module are also
  automatically imported when the GridLAB-D Python interface is started. For
  more information on the `gridlabd` module, see `Python`.

### Example

The following example outputs the current version information.

```
#begin python
output(version())
#end
```

----

## Curl

```
#curl <url> <file>
```

This is synonym of the `#wget` macro.

----

## Debug

```
#debug <message>
```

The `#debug` macro outputs a message to the debugging stream.

### Example

```
#debug This is a debugging message
```

----

## Define

```
#define <variable-name>=<value>
```

The #define macro is used to define a new variable.

### Example

```
#define NAME=value
``` 

### Caveats 

Normally, one can only define a variable that isn't already defined. If you
need to loosen this restriction, use the `strictnames` global variable to
disable protection of existing variables. Otherwise, you must use `#set` to
set the value of an existing variable.

----

## Error

```
#error <message>
```

The `#error` macro outputs a message to the error stream.

### Example

```
#error This is an error message
```

----

## Exec

```
#exec <command>
```

The `#exec` macro is similar to the `#system` macro, except that it will cause
the load to fail if the command has a non-zero exit code. `#exec` also redirects
the command output through the normal GridLAB-D streams, i.e., `stdout` goes to
normal message output and `stderr `goes to error message output.

----

## Flush

```
#flush
```

Flushes the output streams to disk.

----

## For

```
#for <var> in <list>
...
#done
```

The `#for` macro causes the parser to loop through a section of GLM multiple
time with the specified global `<var>` set to each of the space-delimited
entries in `<list>`.

### Example

The following example creates three different random number generators:

```
class random_source 
{
  randomvar value;
}
#for PDF in normal(1,0) uniform(0,1) triangle(-1,1)
object random-source 
{
  value "type:$PDF; refresh:1min";  
}
#done
```

### Caveat

For loops cannot be nested at this time. Also, the maximum length of the input
line is 65535 characters, which implicitly limits the maximum number of items
that can looped over.

----

## Gridlabd

```
#gridlabd <options>
```

The `#gridlabd` macro is similar to running the `#exec gridlabd <options>
`macro, except that it ensures the simulation it runs is exactly the same
version as the caller. Unlike `#exec gridlabd <options>`, this macro ignores
the `PATH` environment variable.

----

## If

```
#if <value1> <comparison> <value2>
...
[#elif
...]
[#else
...]
#endif
```

The `#if` macro introduces a conditional section of a GLM file. The `#elif`, `#else`
and `#endif` macros are used to introduce the alternative section(s) and
terminate the conditional section.

Valid comparisons are 
- `==` 
- `!=`
- `<`
- `<=`
- `>`
- `>=`
- `in`
- `not_in`

### Example

```
#ifdef ${VAR} == yes
#print VAR == "yes"
#else
#print VAR != "yes"
#endif
```

### Caveats

Prior to GridLAB-D version 4.2.1, `value1` is interpreted as a variable name
by default. This behavior is controlled by `literal_if`. As of version 4.2.1,
the value of `literal_if` is `TRUE`. To recover the behavior prior to version
4.2.1, set `literal_if` to `FALSE`. 

If the variable is undefined, you may use the `relax_undefined_if` global
variable to relax the constraint that the variable must be defined to
complete the test.

----

## Ifdef

```
#ifdef <name>
...
[#else]
...
#endif
```

The `#ifdef` macro is used to conditionally process GLM lines when the variable
`<name>` is defined. This is the opposite of the `#ifndef` macro.

### Example

```
#ifndef YES
#print yes
#else
#print no
#endif
```

----

## Ifexist

```
#ifexist <path-name>
...
[#else]
...
#endif
```

or

```
#ifexist "<path-name>"
...
[#else]
...
#endif
```

The `#ifexist` macro is used to conditionally process GLM lines when a file is
found.

### Example

```
#ifexist "myfile.glm"
#print found it
#endif
```

----

## Ifmissing

```
#ifmissing <path-name>
...
[#else]
...
#endif
```

or

```
#ifmissing "<path-name>"
...
[#else]
...
#endif
```

The `#ifmissing` macro is used to conditionally process GLM lines when a file is
not found.

### Example

```
#ifmissing "myfile.glm"
#print didn't find it
#endif
```

----

## Ifndef

```
#ifndef <name>
...
[#else]
...
#endif
```

The `#ifndef` macro is the opposite of the `#ifdef` macro.

### Example

```
#ifndef YES
#print no
#else
#print yes
#endif
```

----

## Include

```
#include "file-name"
#include <library-name>
#include [url]
#include using(<name1>=<value1>,<name2>=<value2>,...,<nameN>=<valueN>) <location>
```

The `#include` macro inserts the file found at `<location>` into the current GLM
stream processed by the loader. If the `using()` option is included, the
parameter list specified is parsed to set global variables used while
processing the include file.

The `#include using(<parameters>) "file-name"` syntax is equivalent to `#insert
file(<parameters>)`.

### Example

The following includes `my-file.glm` in the current GLM loader stream.

```
#include "my-file.glm"
```

### Caveat

GLM files found in the `${GLD_ETC}` folder are automatically loaded before
files located in the current folder. To force load a local file use the
current folder path, e.g.,

```
#include "./my-file.glm"
```

----

## Input

```
#input "filename.ext" [options ...]
```

The `#input` macro allows a non-GLM file to be input inline using automatic
import file format conversion with options.
See [Arras Energy Converters](https://github.com/arras-energy/converters) for
details.

### Example

The following example converts the file data.csv to house.glm using the
converter `csv-ami2glm-house.py` with the `heating_setpoint` property set to
`72 degF`:

```
module powerflow;
object meter 
{
    name main;
    bustype SWING;
    nominal_voltage 120.0;
    phases ABCN;
#input "data.csv" -f ami -t house heating_setpoint=72degF
}
```

----

## Insert

```
#insert name(var1=value1, var2=value2, ..., varN=valueN)
```

The `#insert` macro allows a GLM file to be included with parameters set as
global variables during the include. The macro is equivalent to

```
#include using(var1=value1, var2=value2, ..., varN=valueN) "_name_.glm"
```

----

## On exit

```
#on_exit EXITCODE COMMAND
```

When this macro is encountered, an exit handler is added when the simulation
exits with exitcode. Exit handlers are run only when the simulation has
completed all post simulation processing and is about to exit. The exit
process is suspended until the result of the exit handler(s) are obtained.
The exit code of the exit handler is then used as the exit code of the
simulation.

If multiple exit handlers are specified, they will be called in the order in
which they are listed. If an exit handler returns a non-zero exit code, the
exit handling sequence is abandoned and the exit code of the simulation is
the exit code of the failed handler. If no errors are encountered, the exit
code `0` is used.

When the value `-1` is used for the exitcode, any non-zero exit condition will
trigger the exit handler.

### Example

The following example run a series of models with `VARIABLE` incremented for
each run

```
// set the initial value to 0
#ifndef VARIABLE
#define VARIABLE=0
#endif

// print the value
#system echo ${VARIABLE}

// run the next value, stopping at 9
#if VARIABLE < 9
#on_exit 0 ${exename} -D VARIABLE=$((${VARIABLE}+1)) ${modelname} &
#endif
```

which produces the output

```
0
1
2
3
4
5
6
7
8
9
```

----

## Option

GLM:

```
#option KEYWORD
```

The `#option` macro is equivalent to specifying the `--KEYWORD` on the command line.

### Example

The following toggles verbose output

```
#option verbose
```

----

## Output

```
#output "filename.ext" [options ...]
```

The `#output` macro sets up post-processing when a simulation is completed. In
general, output processing work similarly to input processing insofar as
conversion to various file formats are automatically performed using the
automatic format conversion subsystem. Any options provided are simply passed
through to the file conversion routine. See [Arras Energy
Converters](https://github.com/arras-energy/converters) for details.

### Example

The following example generates the default tag image for a GridLAB-D model:

```
#output "test_output_save.png"
```

----

## Print

```
#print <message>
```

The `#print` macro outputs a message to the print stream.

### Example

```
#print This is a output message
```

----

## Save

```
#save "FILENAME.EXT"
```

The `#save` macro write the model to a file in its current state during the load
process.

### Example

The following command save the model is JSON format.

```
#save ${modelname/.glm/.json}
```

----

## Set

```
#set NAME=VALUE
```

The `#set` macro sets the value of an existing global variable. If the
variable is not defined, the `#set` macro will fail.

### Example

```
#set name=value
```

### Caveats

Normally, one can only set a variable that is already defined. If you need to
loosen this restriction, use the strictnames global variable. Otherwise, you
must use #define to define the value of a new variable.

----

## Setenv

```
#setenv NAME=VALUE
```

The `#setenv` macro sets the environment variable `NAME` to `VALUE`.

When GridLAB-D evaluates a global variable, and the global variable is not
found, then GridLAB-D will attempt to resolve the name using the environment
variables.

### Example

```
#setenv name=value
```

### Caveats

Some environment variables, such a `LD_LIBRARY_PATH` present a security risk
and cannot be set inside a GLM file. In such cases, the environment variable
must be set by the shell that calls GridLAB-D.

----

## Sleep

```
#sleep MILLISECONDS
```

The `#sleep` macro causes the GLM loader to pause for `MILLISECONDS`.

### Example

The following pauses the loader for 1 second.

```
#sleep 1000
```

### Caveat

If the sleep value is invalid, no error is returned and the loader does not
pause. If a signal was received that was routed to a signal-catching function
for the duration indicated, no error is returned, and the sleep process is
not completed.

----

## Start

```
#start COMMAND
```

The `#start` macro runs `COMMAND` in the background and immediately returns. A
zero exit code indicates that the process was started ok. A non-zero exit
code will cause the GLM load to fail.

### Example

The following command starts the GridLAB-D daemon process.

```
#start gridlabd --daemon
```

----

## Subcommand

```
#SUBCOMMAND [OPTIONS ...]
```

All subcommands can be executed by passing through the macro interpreter. The
general syntax takes the macro and prepends `gridlabd-` before calling the
subcommand script installed in `${GLD_BIN}`.

The `stdout` stream is piped to the GridLAB-D output stream and `stderr` is piped
to the GridLAB-D error stream.

### Example

```
#aws s3 ls
```

----

## System

```
#system COMMAND
```

The `#system` macro executes `COMMAND` in the GridLAB-D system environment's
shell. If the command does not specify the full path to an executable, then
it must be found in the `PATH` environment.

### Example

```
#system pwd ; ls -l
```

The return code is ignored. If you need to have the GLM load fail when the
return code is non-zero, use the `#exec` macro instead.

----

## Verbose

```
#verbose <message>
```

The `#verbose` macro outputs a message to the verbose stream.

### Example

```
#verbose This is a debugging message
```

----

## Version

```
#version [-{lt,le,eq,ge,gt,ne}] {MAJOR.MINOR.PATCH,NUMBER,BRANCH} ...
```

The `#version` macro checks the version number. If the version that is running
does not satisfy the criteria given by the macro, the load fails with the
error

```
ERROR [INIT]: version <current-version-info> does not satisfy the requirement <given-version-info>
```

Three aspects of the version can be checked. They are the version number,
e.g., `4.2.1`, the build number, e.g., `191226`, or the branch name, e.g.,
`develop`. The check can require the current version be strictly less
that (`-lt`), less than or equal (`-le`), equal (`-eq`), greater than or
equal (`-ge`), strictly greater than (`-gt`), or not equal (`-ne`). If
omitted the test is `-eq`.

Multiple tests may be specified, in which case the tests conjunction is the or
operation, i.e., either one may be true for the test to succeed. To achieve
an and operation, simply use the macro multiple times.

### Example

The following example checks that the version is greater or equal `4.2.1` or
the build number is is greater than `191225` and the branch is `develop`.

```
#version -ge 4.2.1 -gt 191225
#version develop
```

----

## Wait

```
#wait
```

The `#wait` macro wait on a task started by the #start macro in the
background. The loader will continue when all the started tasks have exited.
If any task exits with an error, the wait command fails and the GLM load will
fail.

### Example

The following command starts the GridLAB-D daemon process and waits for it to
terminate.

```
#start gridlabd --daemon
#wait
```

----

## Warning

```
#warning MESSAGE
```

The `#warning` macro outputs a message to the warning stream.

### Example

```
#warning This is a warning message
```

----

## Wget

```
#wget <url>
```

The `#wget` macro downloads a file from a server using HTTP.

### Example

```
#wget http://example.org/index.html
```

### Caveats

The only protocol support is HTTP. HTTPS is not supported.

No header options are available.

----

## Write

```
#write FILENAME.EXT CLASSLIST:PROPERTYLIST
```

The write macro dumps the current model to a CSV, JSON, or GLM file based on
the filename extension, i.e., where `EXT` is one of csv, json, or glm,
respectively. Data is only be dumped from the classes specified in `CLASSLIST`
and `PROPERTYLIST` where classes and properties are comma delimited.

Data is dumped with id, class, and name properties.

### Example

The following example generates a CSV, JSON, and GLM file containing the

```
class test1
{
    randomvar x;
}
class test2
{
    randomvar x;
    randomvar y;
}
object test1:..5
{
    x "type:uniform(0,1)";
}
object test2:..5
{
    x "type:normal(0,1)";
    y "type:uniform(0,1)";
}
#write /tmp/write.csv test1,test2:x,y
```

The CSV output looks something like this:

```
id,class,x,y
0,test1,"test1:0",0.970795,
1,test1,"test1:1",0.053650,
2,test1,"test1:2",0.845886,
3,test1,"test1:3",0.024933,
4,test1,"test1:4",0.111084,
5,test2,"test2:5",-0.696906,0.222839
6,test2,"test2:6",0.825553,0.745361
7,test2,"test2:7",1.151177,0.632141
8,test2,"test2:8",0.213561,0.701630
9,test2,"test2:9",-0.747831,0.709808
```

The JSON output looks something like this:

```
[
  {
    "name" : "test1:0",
    "class" : "test1",
    "id" : "0",
    "x" : "0.970795"
  }
  {
    "name" : "test1:1",
    "class" : "test1",
    "id" : "1",
    "x" : "0.053650"
  }
  {
    "name" : "test1:2",
    "class" : "test1",
    "id" : "2",
    "x" : "0.845886"
  }
  {
    "name" : "test1:3",
    "class" : "test1",
    "id" : "3",
    "x" : "0.024933"
  }
  {
    "name" : "test1:4",
    "class" : "test1",
    "id" : "4",
    "x" : "0.111084"
  }
  {
    "name" : "test2:5",
    "class" : "test2",
    "id" : "5",
    "x" : "-0.696906",
    "y" : "0.222839"
  }
  {
    "name" : "test2:6",
    "class" : "test2",
    "id" : "6",
    "x" : "0.825553",
    "y" : "0.745361"
  }
  {
    "name" : "test2:7",
    "class" : "test2",
    "id" : "7",
    "x" : "1.151177",
    "y" : "0.632141"
  }
  {
    "name" : "test2:8",
    "class" : "test2",
    "id" : "8",
    "x" : "0.213561",
    "y" : "0.701630"
  }
  {
    "name" : "test2:9",
    "class" : "test2",
    "id" : "9",
    "x" : "-0.747831",
    "y" : "0.709808"
  }
]
```

The GLM output looks something like this:

```
// writefile(char *fname='/tmp/write.glm', char *specs='test1,test2')
// modelname /tmp/test.glm
modify test1:0.x "0.970795";
modify test1:1.x "0.053650";
modify test1:2.x "0.845886";
modify test1:3.x "0.024933";
modify test1:4.x "0.111084";
modify test2:5.x "-0.696906";
modify test2:5.y "0.222839";
modify test2:6.x "0.825553";
modify test2:6.y "0.745361";
modify test2:7.x "1.151177";
modify test2:7.y "0.632141";
modify test2:8.x "0.213561";
modify test2:8.y "0.701630";
modify test2:9.x "-0.747831";
modify test2:9.y "0.709808";
```

### Caveat

Note that CSV data creates columns for all properties but uses empty cells for
properties that are not defined to the specified class. In contrast, JSON and
GLM files will omit any properties that are not defined for the given class.
This implies that erroneous properties are not detected and will not result
in an error or warning message.

----

# **Objects**

----

## Events

```
  object class {
    on_init "command";
    on_precommit "command";
    on_presync "command";
    on_sync "command";
    on_postsync "command";
    on_commit "command";
    on_finalize "command";
  }
```

Objects can be assigned external event handlers using the on_* load method.
The following events may be handled: `init`, `precommit`, `presync`, `sync`,
`postsync`, `commit`, `finalize`.

### Python support

If the command is to be processed in the Python environment, use the `python:`
prefix, e.g.,

```
object name 
{
  on_sync "python:module.method";
}
```

In this case, the function method in the python3 module must be defined as
follows:

```
def method(name,t1):
  // process object name at timestamp t1
  // return t2 for time of upcoming event
  // return gridlabd.NEVER for no upcoming event
  // return gridlabd.INVALID for error
```

### Shell environment

The following global variables are copied to the shell environment when the
script is called

```
''clock'': CLOCK is the global clock
''hostname'': HOSTNAME is the server hostname
''server_portnum'': PORT is the server port number
''object_name'': OBJECT is the object name
```

### Example

```
module residential;
#set suppress_repeat_messages=0
#option server
module tape;
clock 
{
  starttime '2000-01-01 00:00:00';
  stoptime '2000-01-01 01:00:00';
}
object house 
{
  name house_1;
  on_init "echo init clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  on_precommit "echo precommit clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  on_presync "echo presync clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  on_sync "echo sync clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  on_postsync "echo postsync clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  on_commit "echo commit clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  on_finalize "echo finalize clock=$CLOCK hostname=$HOSTNAME port=$PORT object=$OBJECT";
  object recorder 
  {
    property air_temperature;
    interval 300;
    file air_temperature.csv;
  };
}
``` 

----

# **Properties**

----

## Python

```
class <class-name> 
{
  python <property-name>;
}
object <class-name> 
{
  <property-name> <type(<value>);
}
```

The python property type support general python objects. Although any type of
object is supported, only those that implement the python str method as
useful because GridLAB-D require the str() to generate the values for data
exchange.

### Example

```
class test
{
  python py_object;
}
object test
{
  py_object None;
}
object test
{
  py_object int(1);
}
object test
{
  py_object float(0.0);
}
object test
{
  py_object float(1.23);
}
object test
{
  py_object str('text');
}
object test
{
  py_object list([1,2,3]);
}
object test
{
  py_object dict(a=1,b=2,c=3);
}
```

----

## Randomvar

```
class <class-name> 
{
    randomvar <property-name>;
}
object <class-name> 
{
    <property-name> 
    {
        <value> | type:<distribution>(<parameters>); 
        [min:<lower-bound>;] 
        [max:<upper-bound>;] 
        [refresh: <update-rate>] 
        [state:<seed>] 
        [correlation:[<object-name>.]<property-name>[*<scale>[+<bias>]]]
        [integrate;]
    };
}
```

The `randomvar` property type implements a pseudo-random value that changes
periodically according to the `<distribution>` given. The meaning of the
`<parameters>` depends on the `<distribution>` chosen. The distributed may be
truncated at the `<lower-bound>` and `<upper-bound>`. The frequency of the
updates is given by the `<update-rate>`.

Correlated random variables are generated using the equation $x = x_1 +
x_0 \times scale + bias$ where $x_0$ is the current value obtained from
`<object-name>.<property-name>` and $x_1$ is the sample from
`<distribution>(<parameters>)`.

If `integrate` is specified, each new random value is added the current value.

For details on the supported distributions, see Random.

### Example

The following example generates two standard random Gaussian that are 90%
anti-correlated.

```
class example 
{
    randomvar x;
    randomvar y;
}
module tape;
object example 
{
    name my_object;
    x {type:normal(0.0,1.0): min:-3.0, max:+3.0; refresh:1.0min;};
    y {type:normal(0.0,0.1); min:-3.0; max:+3.0; refresh:1.0min; correlation:my_object.x*-0.9};
    object recorder {
        property "x,y";
        file "example.csv";
        interval -1;
    };
}
```

### Caveat 

The order in which the random variables is defined is important to creating
correlations. As a result, the correlation specification must refer to an
existing random variable. In addition, because each random variable may
depend on only one other random variable, the standard method of creating $N
\gt 2$ correlated random variables is not supported directly. Instead, a
 cascade of $N = 2$ random variables must be defined. This can be
 accomplished by performing Gauss elimination on the Cholesky decomposition
 of the covariance matrix to obtain a bi-diagonal matrix of the form

```
(     s[1]^2          0          0          0          0 )
(   s[1]s[2]     s[2]^2          0          0          0 )
(          0   s[2]s[3]     s[3]^2          0          0 )
(          0          0          .          .          0 )
(          0          0          0 s[N-1]s[N]     s[N]^2 )
```

----

## String

```
class class-name 
{
  string property-name;
}
object class-name 
{
  property-name "property-value";
}
```

or
```
object class-name 
{
  property-name """ '''"""multiline
value"""''' """;
  }
```

The string property allows storage and import/export of strings of arbitrary
length.

----

## Timestamp

```
class <class-name> 
{
  Timestamp <property-name>;
}
object <class-name> {
  <property-name> "<date-value>";
}
```

Timestamp properties can be specified in US, EU, ISO, and ISO 8601 formats, as
indicated by the Dateformat (Global) variable.

The following ISO 8601 date/time formats are now supported for all timestamp
value inputs:

```
yyyy-mm-ddTHH:MM:SS[.SSSSSSSSS]Z
yyyy-mm-ddTHH:MM:SS[.SSSSSSSSS]{+,-}HH:MM
```

### Caveat

GridLAB-D does not currently support output in ISO 8601 format
"""
