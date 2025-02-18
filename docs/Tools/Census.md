[[/Tools/Census]] -- Census data access

Syntax: gridlabd census STATE [COUNTY]

The census tool obtains Census Bureau data about counties

Data obtained include the following:

* `state`: state FIPS code

* `county`: county FIPS code

* `gcode`: NREL county $g$-code

* `tzspec`: timezone specification for state and county

Caveats:

The value of `STATE` must be the two character abbreviation, e.g., `CA`.  The
value `COUNTY` may be a county name or a `regex` pattern to match multiple
counties.  The defaults value for `COUNTY` is `.*`, which will match all
counties in the state.

Some states have multiple timezones. The `tzspec` specification for states
that have more than one timezone is given for the more populous portion of
the state. 



# Classes

## Census

Census object class

### `Census(state:str, county:str)`

Get census data

Arguments:

* `state`: State for which census data is downloaded

* `county`: County regex for which census data is downloaded


### `Census.dict() -> dict`

Get a dict of the census data obtained

### `Census.length() -> int`

Get the number counties matching the county name given

### `Census.list() -> list`

Get a list of counties matching the county name given

---

## CensusError

Census exception

# Functions

## `test(state:str, county:str) -> None`

Test census data access

Arguments:

* `state`: state to test

* `county`: county name pattern to test

Returns:

* `int`: failed tests

* `int`: counties tested


# Constants

* `FIPS_STATES`
* `TIMEZONES`

# Modules

* `gridlabd.framework`
* `os`
* `pandas`
* `re`
* `sys`
