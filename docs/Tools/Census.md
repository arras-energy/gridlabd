[[/Tools/Census]] -- Census data access

Syntax: gridlabd census COUNTRY STATE [COUNTY]

The census tool obtains Census Bureau data about counties

Data obtained include the following:

* `state`: state FIPS code

* `county`: county FIPS code

* `gcode`: NREL county $g$-code

* `pgode`: HIFLD county $p$-code

* `tzspec`: timezone specification for state and county

Caveats:

The value of `STATE` must be the two character abbreviation, e.g., `CA`.  The
value `COUNTY` may be a county name or a `regex` pattern to match multiple
counties.  The defaults value for `COUNTY` is `.*`, which will match all
counties in the state.

Some counties have multiple timezones. The `tzspec` specification for counties
that have more than one timezone is given for the more populous/larger portion of
the county. The following counties are affected by this issue:

* Florida: Gulf
* Idaho: Idaho
* Nebraska: Cherry
* North Dakota: McKenzie, Dunn, Sioux
* Oregon: Malheur
* South Dakota: Cherry

See also:

* [[/Tools/Framework]]



# Classes

## Census

Census object class

### `Census(country:str, state:str, county:str)`

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
