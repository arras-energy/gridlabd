[[/Tools/Powerplant]] -- Powerplant data tool

Syntax: gridlabd powerplant COUNTRY STATE COUNTY [OPTIONS ...]

Options:

* `-o|--output=FILENAME`: specify GLM or CSV output to FILENAME

Description:

The `powerplant` tool read the HIFLD database for powerplant data in the
specified COUNTY, STATE, and COUNTY.

Example:

The following write the powerplant data for Grant County WA to `stdout`:

~~~
gridlabd powerplant US WA Grant
~~~

See Also:

* [[/Tools/Framework]]
* [https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::power-plants-2]




# Classes

## PowerPlantError

Powerplant exception

---

## Powerplant

Powerplant class

### `Powerplant(country:str, state:str, county:str, planttype:str)`

Create a powerplant dataset

Arguments:

* `country`: only `'US'` is supported

* `state`: state name (abbreviated)

* `county`: country name regex pattern (e.g., starting with)

* `planttype`: plant type filter


### `Powerplant.to_glm(fh:str) -> None`

Generate GLM file from powerplant data

Arguments:

* `fh`: file name or file handle


# Functions

## `main() -> None`

Main process

Arguments:

* `argv`: command line argument list

Returns:

* `int`: exit code (see `framework.E_*` codes)


---

## `test() -> None`

Test procedure

Returns:

* `int,int`: number failed and number tested


# Constants

* `CONVERTERS`

# Modules

* `gridlabd.census`
* `gridlabd.framework`
* `json`
* `os`
* `pandas`
* `requests`
* `sys`
