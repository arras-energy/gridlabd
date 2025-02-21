[[/Tools/Timeseries]] -- Timeseries tools


# Functions

## `project_daterange(source:list, target:list, start:Union, end:Union, align:bool) -> dict`

Map dates to a new date range

Arguments:

* `source`: date/time series to map to

* `target`: date/time series to map from

* `align`: mapping alignment

Returns:

* `dict`: mapping from target to source

Description:

Maps dates from a target range to a source range using the alignment
provided, if any.  Valid alignments are:

* `None`: the mapping is based on the start date (e.g., simple wrapped map)

* `'year'`: the mapping is based on the day of the year (day of year aligned)

* `'week'`: the mapping is based on the day of week (day of week of year aligned)


# Constants


# Modules

* `datetime`
* `pandas`
* `sys`
