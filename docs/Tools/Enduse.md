[[/Tools/Enduse]] -- Access enduse load data from NREL

Syntax: gridlabd enduse COUNTRY STATE COUNTY [OPTIONS ...]

Options:

* `--local`: use local timezone

* `--electrification=ENDUSE:FRACTION[,...]`: specify enduse electrification

* `--list=FEATURE`: list of available features

* `--start`: set the start date (default is `2018-01-01 00:00:00 EST`)

* `--end`: set the end date (default is `2019-01-01 00:00:00 EST`)

* `--type=PATTERN[,...]`: specify the building type(s)

Description:

The `enduse` tool generates enduse load data for buildings at the specified
location.

Valid values for `FEATURE` are `sector`, `type`, `country`, `state`, `county`, and
`enduse`. If `state` is requests the COUNTRY must be specified. If `county` is 
requested, the COUNTRY and STATE must be specified.



# Classes

## Enduse

Enduse class

### `Enduse(country:str, state:str, county:str | None, building_types:list[str] | None, weather:str, timestep:str | None, electrification:dict)`

Access building enduse data

Arguments:

* `country`: country code (e.g., "US")

* `state`: state abbreviation (e.g., "CA")

* `county`: County name pattern (must by unique)

* `building_type`: Building type regex (i.e., pattern matches start by
default). See `BUILDING_TYPE` for valid building types

* `timestep`: timeseries aggregate timestep (default '1h')

* `electrification`: electrification fractions for enduses (see ENDUSES)


### `Enduse.has_buildingtype(building_type:str) -> bool`

Checks whether data include building type

Argument:

* `building_type`: building type to check

Returns:

* `bool`: building type found


### `Enduse.sum() -> bool`

Get total enduse energy for building_type

Argument:

* `building_type`: building type to check

Returns:

* `bool`: building type found


---

## EnduseError

Enduse exception

# Functions

## `main(argv:list) -> int`

Enduse main routine

Arguments:

* `argv`: argument list (see Syntax for details)

Returns:

* `int`: exit code


# Constants

* `BUILDING_TYPE`
* `CONVERTERS`
* `ENDUSES`
* `SECTORS`
* `TYPES`
* `URL`
* `WEATHER`
* `types`

# Modules

* `gridlabd.census`
* `gridlabd.eia_recs`
* `gridlabd.framework`
* `json`
* `os`
* `pandas`
* `re`
* `sys`
