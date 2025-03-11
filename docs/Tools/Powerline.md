[[/Tools/Powerline]] -- Powerline data tool

Syntax: `gridlabd powerline COUNTRY [STATE [COUNTY]] [OPTIONS ...]

Options:

* `--consolidate={state,county}`: substation consolidate level

* `-o|--output=FILENAME`: output network model to FILENAME

Description:

The `powerline` tool reads the HIFLD transmission line data repository and
generates a network model for the specified region.  The output FILENAME may
a `.glm` or `.json` file.  

If substation consolidation is included, then all the substations at the
specified level are consolidated into a single node with all substation loads
and generation connected at that node.

Example:

See also:

* [[/Tools/Powerplant]]
* [[/Tools/Substation]]
* [HIFLD transmission line data repository](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::transmission-lines/about)



# Classes

## Powerline

Powerline class implementation

### `Powerline(args:list, consolidate:str, kwargs:dict)`

Create network class object

Arguments:

* `args`: substation class arguments (e.g., `country`, `state`, `county`)

* `consolidate`: consolidation level desired (e.g., `state`, `county`)

* `kwargs`: substation class arguments (e.g., filters)


### `Powerline.write_glm(outfile:str) -> None`

Write GLM

Arguments:

* `outfile`: output file name


---

## PowerlineException

Powerline class exception handler

# Functions

## `main() -> None`

Main routine

Arguments:

* `argv`: command line arguments


---

## `test() -> None`

Test routine

# Constants

* `CONVERTERS`

# Modules

* `geojson`
* `gridlabd.framework`
* `gridlabd.resource`
* `gridlabd.substation`
* `gzip`
* `io`
* `os`
* `pandas`
* `random`
* `requests`
* `sys`
