[[/Tools/Location]] -- Location tool

Syntax: `gridlabd location [OPTIONS ...] [FILENAME=KEY[:VALUE][,...] ...]`

Options:

* `--debug`: enable debug traceback on exception

* `--quiet`: suppress error messages

* `--silent`: suppress all error messages

* `--warning`: suppress warning messages

* `--verbose`: enable verbose output, if any

* `--system[=LOCATION]`: get/set the default location

* `--find[=LOCATION]`: get location settings

Description:

The `location` tool allows configuration of the location of a model.

The `location` tool `--system` option is used to setup the system's default
location for models when not location data is not specified in the model.
When values are change, the location data is returned and the new location
is stored in `GLD_ETC/location_config.glm

The `location` tool `--find` options can identify the current location of a
system or a location based on partial information.

The keys and globals handled by the `location` tools include the following:

* `latitude`: the location's latitude


* `longitude`: the location's longitude

* `number`: the location's street number, if any

* `street`: the location's street name

* `zipcode`: the location's postal code

* `city`: the location's city

* `county`: the location's county

* `state`: the location's state

* `region`: the location's region

* `country`: the location's country

Examples:

Get the current location

    gridlabd location --find

Display the default location

    gridlabd location --system

Set the location in a model file

    gridlabd location ieee123.json=country:US,state:CA,county:Kern,city:Bakersfield


