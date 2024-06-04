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
file. The time index column name is specified by the `indexname` property and
it must be the first column of the CSV file. The default `indexname` is
`timestamp`.

When an error is encountered, the `on_error` property is used to determine
what happen, if anything, i.e., `IGNORE`, `WARN`, or `STOP`.  The `status`
property provide an indication of `multiplayer` status.

# Caveats

Unlike `player`, the `multiplayer` object does not support triggers, loops, 
of differential timestamps.

Empty CSV fiels are not supported and will result in `missing data` errors.

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
