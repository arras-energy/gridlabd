[[/Tools/Enduse]] -- Access enduse load data from NREL

Syntax: gridlabd enduse COUNTRY STATE COUNTY [OPTIONS ...]

Options:

* `--local`: use local timezone

* `--electrification=ENDUSE:FRACTION[,...]`: specify enduse electrification

* `--list=FEATURE`: list of available features

* `--start`: set the start date (default is `2018-01-01 00:00:00 EST`)

* `--end`: set the end date (default is `2019-01-01 00:00:00 EST`)

* `--type=PATTERN[,...]`: specify the building type(s)

* `--model=FILENAME`: specify the GLM or JSON file to generate

* `--player=FILENAME`: specify the CSV file to generate

* `--weather={actual,typical}`: select weather data to use

Description:

The `enduse` tool generates enduse load data for buildings at the specified
location.

Valid values for list `FEATURE` are `sector`, `type`, `country`, `state`, `county`, and
`enduse`. If `state` is requests the COUNTRY must be specified. If `county` is 
requested, the COUNTRY and STATE must be specified.

The `player` FILENAME must include `{building_type}` if more than one `type`
is specified.

When `actual` whether is used, the `timeseries` alignment `week` is used. See
`timeseries.project_daterange()` for details.

Example:

The following command generates a GLM and CSV file for mobile homes in
Snohomish County, Washington:

~~~
gridlabd enduse US WA Snohomish --player='test_enduse_{building_type}.csv' --model=test_enduse_opt.glm --type=MOBILE 
~~~



# Classes

## Enduse

Enduse class

### `Enduse(country:<I>str</I>, state:<I>str</I>, county:<I>str | None</I>, building_types:<I>list[str] | None</I>, weather:<I>str</I>, timestep:<I>str | None</I>, electrification:<I>dict</I>)`

Access building enduse data

Arguments:

* `country`: country code (e.g., "US")

* `state`: state abbreviation (e.g., "CA")

* `county`: County name pattern (must by unique)

* `building_type`: Building type regex (i.e., pattern matches start by
default). See `BUILDING_TYPE` for valid building types

* `timestep`: timeseries aggregate timestep (default '1h')

* `electrification`: electrification fractions for enduses (see ENDUSES)


### `Enduse.has_buildingtype(building_type:<I>str</I>) -> <I>bool</I>`

Checks whether data include building type

Argument:

* `building_type`: building type to check

Returns:

* `bool`: building type found


### `Enduse.sum(building_type:<I>str</I>, enduse:<I>str</I>) -> <I>bool</I>`

Get total enduse energy for a building type

Argument:

* `building_type`: building type to check (see `BUILDING_TYPES`)

* `enduse`: enduse load category (see `ENDUSES`)

Returns:

* `bool`: building type found


### `Enduse.to_glm(glmname:<I>str</I>, glmdata:<I>dict</I>) -> <I>None</I>`

Write GLM objects created by players

### `Enduse.to_player(csvname:<I>str</I>, building_type:<I>str</I>, enduse:<I>str</I>) -> <I>dict</I>`

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

## `main(argv:<I>list</I>) -> <I>int</I>`

Enduse main routine

Arguments:

* `argv`: argument list (see Syntax for details)

Returns:

* `int`: exit code


---

## `test() -> <I>None</I>`

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
* `WEATHER_URL`
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
