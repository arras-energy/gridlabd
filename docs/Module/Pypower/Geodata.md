[[/Module/Pypower/Geodata]] -- PyPower geodata object

# Synopsis

~~~
class geodata 
{
    char1024 file; // geodata file name
    char256 target; // geodata target class and property, e.g., CLASS:PROPERTY
}
~~~

# Description

A `geodata` object can be used to apply values to properties of object
according to the geographic location. The selection of the value to apply is
based on the nearest location in the `geodata` file. The format of the file
is a time-series, with locations encoded using geohashes in columns, e.g.,

~~~
timestamp,9mugye,9mupxg
2018-01-01 00:00:00,10,11
2018-01-01 01:00:00,12,13
2018-01-01 02:00:00,14,15
~~~

Only double values may be applied using `geodata`.

# Caveat

Some object properties are updated after the `precommit` event that processes
geodata. Consequently, any geodata written to these objects will be
overwritten by subsequent events processed by those objects. This is notably
true for `bus` and `branch` objects. If you want to change power injections, 
you should process geodata for the child objects that update them, e.g., `load`,
`powerplant`, or `powerline`.

# Example

The following example applies the values in the file `geodata_load_P.csv` to the
values of `P` is all object of class `load`.

~~~
object pypower.geodata
{
    file "geodata_load_P.csv";
    target "load::P";
}
~~~

# See Also

* [[Module/Pypower]]
