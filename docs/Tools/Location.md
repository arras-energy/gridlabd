[[/Tools/Location]] -- Location tool

Syntax: `gridlabd location [OPTIONS ...] [FILENAME=KEY[:VALUE][,...] ...]`

Options:

* `--debug`: enable debug traceback on exception

* `--find[=KEY[:VALUE][,...]]`: get location settings

* `--format=FORMAT[,OPTION[:VALUE[,...]]]

* `--quiet`: suppress error messages

* `--silent`: suppress all error messages

* `--system[=KEY[:VALUE][,...]]`: get/set the default location

* `--verbose`: enable verbose output, if any

* `--warning`: suppress warning messages

Description:

The `location` tool allows configuration of the location of a model.

The `location` tool `--system` option is used to setup the system's default
location for models when not location data is not specified in the model.
When values are change, the location data is returned and the new location
is stored in `GLD_ETC/location_config.glm

The `location` tool `--find` options can identify the current location of a
system or a location based on partial information.

Location setting on `FILENAME` will be performed in place, i.e., the file will
first be read and the it will be written with the new values. The result
output to stdout will be the previous values.

The keys and globals handled by the `location` tools include the following:

* `latitude`: the location's latitude

* `longitude`: the location's longitude

* `zipcode`: the location's postal code

* `city`: the location's city

* `county`: the location's county

* `state`: the location's state

* `region`: the location's region

* `country`: the location's country

Caveat:

Although the `--find` option allows multiple addresses to be resolved, it is
certainly not efficient to do more than a few queries this way. If you need
to resolve large number of addresses then you should use the batch feature of
the `geocoder` module.

Examples:

Get the current location

    gridlabd location --find

Display the default location

    gridlabd location --system

Set the location in a model file

    gridlabd location ieee123.json=country:US,state:CA,county:Kern,city:Bakersfield




# Classes

## LocationError

Location exception

# Functions

## `find() -> dict`

Find location data

Arguments:

* `kwargs`: Partial location data (see `system()`). None return IP location.

Returns:

* Location data


---

## `get_location() -> dict`

Get location data in file

Arguments:

* `file`: file from which to get location data

Returns:

* Current values


---

## `main() -> int`

Main location routine

Arguments:

* `argv`: command line argument list

Returns:

* Exit code


---

## `set_location() -> dict`

Set location in file

Arguments:

* `file`: file in which to set location data

* `**kwargs`: location data

Returns:

* Previous values


---

## `system() -> dict`

Get/set system location settings

Arguments:

* `latitude`: new latitude

* `longitude`: new longitude

* `number`: new street number

* `street`: new street name

* `zipcode`: new zipcode

* `city`: new city

* `county`: new county

* `state`: new state

* `region`: new region

* `country`: new country

Returns:

* previous location settings


# Constants

* `LOCATIONKEYS`
* `PROVIDERCONFIG`

# Modules

* `gridlabd.framework`
* `datetime`
* `gridlabd.edit`
* `geocoder`
* `json`
* `os`
* `sys`
