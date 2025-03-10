[[/Tools/Enduse]] -- Access enduse load data from NREL

Syntax: gridlabd enduse COUNTRY STATE COUNTY [OPTIONS ...]

Options:

* `--local`: use local timezone

* `--electrification=ENDUSE:FRACTION[,...]`: specify enduse electrification

* `--list=FEATURE`: list of available features

* `--start`: set the start date (default is `2018-01-01 00:00:00 EST`)

* `--end`: set the end date (default is `2019-01-01 00:00:00 EST`)

* `--timestep=FREQ`: set the timestep of the date/time range (only 15min or longer
  is available from NREL)

* `--type=PATTERN[:SCALE][,...]`: specify the building type(s) and load scale

* `--model=FILENAME`: specify the GLM or JSON file to generate

* `--player=FILENAME`: specify the CSV file to generate

* `--weather={actual,typical}`: select weather data to use

* `--combine: combine buildings types into a single load

Description:

The `enduse` tool generates enduse load data and models for buildings at the specified
location.

The `player` FILENAME must include `{building_type}` if more than one `type`
is specified.

If the `start` and `end` dates are not specified, then the date range of
enduse load data will be used. The current default data range is the year 2018.

The default CSV filename is `{country}_{state}_{county}_
{building_type}.csv`. The default GLM filename is `{country}_{state}_{county}.glm`.

The default weather is `tmy3`. When `actual` whether is used, the `timeseries`
alignment `week` is used to project actual weather to the current time. See
`timeseries.project_daterange()` for details. 

Valid values for list `FEATURE` are `sector`, `type`, `country`, `state`, `county`, and
`enduse`. If `state` is requests the COUNTRY must be specified. If `county` is 
requested, the COUNTRY and STATE must be specified.

When using `SCALE`, the enduse factors are per building for residential
building types, and per thousand square foot for commercial building types.

Example:

The following command generates GLM and CSV files for detached single family
homes in Snohomish County, Washington in August 2020:

~~~
gridlabd enduse US WA Snohomish --type=SINGLE_FAMILY_DETACHED --start=2020-08-01T00:00:00-08:00 --end=2020-09-01T00:00:00-08:00
~~~

See also:

* [[/Tools/Census]]
* [[/Tools/Framework]]
* [[/Tools/Weather]]



# Classes

## Enduse

Enduse class

### `Enduse(country:str, state:str, county:str | None, building_types:list[str] | None, weather:str, timestep:str | None, electrification:dict, ignore:bool)`

Access building enduse data

Arguments:

* `country`: country code (e.g., "US")

* `state`: state abbreviation (e.g., "CA")

* `county`: County name pattern (must by unique)

* `building_type`: Building type regex (i.e., pattern matches start by
default). See `BUILDING_TYPE` for valid building types

* `timestep`: timeseries aggregate timestep (default '1h')

* `electrification`: electrification fractions for enduses (see ENDUSES)

* `ignore`: ignore download errors


### `Enduse.has_buildingtype(building_type:str) -> bool`

Checks whether data include building type

Argument:

* `building_type`: building type to check

Returns:

* `bool`: building type found


### `Enduse.sum(building_type:str, enduse:str) -> bool`

Get total enduse energy for a building type

Argument:

* `building_type`: building type to check (see `BUILDING_TYPES`)

* `enduse`: enduse load category (see `ENDUSES`)

Returns:

* `bool`: building type found


### `Enduse.to_glm(glmname:str, glmdata:dict) -> None`

Write GLM objects created by players

### `Enduse.to_player(csvname:str, building_type:str, enduse:str) -> dict`

Write player data

Argument:

* `csvname`: name of CSV file

* `building_type`: regex pattern of building types (see TYPES)

* `enduse`: regex pattern for enduses to write to CSV

Returns:

* `dict`: GLM objects needed to access players

The `csvname` should include the `building_type` field, e.g., `mycsv_
{building_type}` if more than one building type matches the
`building_type` pattern.


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


---

## `test() -> None`

Run self-test

Returns:

* `(int,int)`: number of failed test and number of tests performed


# Constants

* `BUILDING_TYPE`
* `CONVERTERS`
* `ENDUSES`
* `ENDUSE_URL`
* `SECTORS`
* `TYPES`
* `WEATHER`
* `WEATHER_COLUMNS`
* `WEATHER_URL`
* `types`

# Modules

* `gridlabd.census`
* `gridlabd.eia_recs`
* `gridlabd.framework`
* `gridlabd.timeseries`
* `json`
* `os`
* `pandas`
* `re`
* `sys`
