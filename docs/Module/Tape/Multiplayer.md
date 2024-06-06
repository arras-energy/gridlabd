[[/Module/Tape/Multiplayer]] -- Multiplayer object

# Synopsis

GLM:

~~~
class multiplayer {
	enumeration {ERROR=3, DONE=2, OK=1, INIT=0} status; // status of multiuplayer
	char32 indexname; // name of index column
	enumeration {STOP=2, WARN=1, IGNORE=0} on_error; // error handling (IGNORE, WARN, STOP)
	method file; // data source
	method property; // target property or object:property
}
~~~

# Description

The `multiplayer` object is used to play multiple properties into an object
from a CSV file simultaneously, rather than using a single property at a time
as `player` does. The `file` property specifies the name of the CSV to use.

The list of properties is provided using the optional `property` method. When
omitted, the list of properties will be read from the first line of the CSV
file. Value may be any allowable string for the specified property's type.
Property names may include units in square braces, e.g., `value[unit]`, which
must be compatible with the unit of the target object's property. Specifying
the units will result in automatic conversion of double and complex values.
Otherwise, all values are assumed to be in the units of the target property,
if any. 

The time index column name is specified by the `indexname` property and it
must be the first column of the CSV file. The default `indexname` is
`timestamp`.

When an error is encountered, the `on_error` property is used to determine
what happens, if anything, when an error is encountered while read data from
the file. Valid values for `on_error` are `IGNORE`, `WARN`, or `STOP`.  The
`status` property provide an indication of `multiplayer` status and will be
set according the result of processing the last record regardless of the
value of `on_error`

# Caveats

Unlike `player`, the `multiplayer` object does not support triggers, loops, 
of differential timestamps.

Empty CSV files are not supported and will result in `missing data` errors.

Unit conversion is only supported for `double` and `complex` properties. Data
is ignored for property types that have underlying double values and may have
units.

# Example

The following example reads three columns of data from a CSV file with the
header row `timestamp,x,y,n`:

~~~
class test
{
	double x;
	double y[s];
	int32 n;
}

module tape
{
	csv_header_type NAME;
}

object test
{
	object multiplayer 
	{
		file "${DIR:-.}/test_multiplayer.csv";
	};
}
~~~

# See also

* [[/Module/Tape/Player]]
