[[/Tools/Substation]] -- Substation tool

Syntax: gridlabd substation [COUNTRY[,...] [STATE[,...] [COUNTY[,...]]]] [OPTIONS ...]

Options:

* `--zipcode=ZIPCODE[,...]`: limit result to substations in ZIPCODE list

* `--status=STATUS[,...]`: limit result to substations having status in STATUS list

* `--fips=FIPS[,...]`: limit result to substations having county fips in FIPS list

* `--latitude=MIN,MAX`: limit result to substations in latitude range

* `--longitude=MIN,MAX`: limit result to substations in longitude range

* `--voltage=MIN,MAX`: limit result to substations in voltage range

* `--lines=MIN,MAX`: limit result to substations having lines in range

* `-o|--output=FILENAME`: output to GLM, CSV, or JSON file

Description:

The `substation` tool accesses substation data for the specified location and substation
characteristics.



# Classes

## Substation

Substation data access class

### `Substation(country:str | list[str], state:str | list[str], county:str | list[str], zipcode:int | list[int], status:str | list[str], fips:str | list[str], latitude:minmax, longitude:minmax, voltage:minmax, lines:minmax)`

Substation data object

Arguments:

* `country`: country filter

* `state`: state filter

* `county`: county filter

* `zipcode`: zipcode filter

* `status`: status filter

* `fips`: fips filter

* `latitude`: latitude range

* `longitude`: longitude range

* `voltage`: voltage range

* `lines`: lines range


### `Substation.to_csv(args:list, kwargs:dict) -> str | None`

Get data as csv

### `Substation.to_dict() -> dict`

Get data as dict

### `Substation.to_glm(filename:str) -> str`

Get data as glm

### `Substation.to_json(args:list, kwargs:dict) -> str | None`

Get data as json

### `Substation.to_list() -> list`

Get data as list

---

## SubstationError

Substation exception handler

---

## minmax

minmax(min, max)

# Functions

## `main(argv:list) -> int`

Main routine

---

## `test() -> None`

Test routine

# Constants

* `CONVERTERS`
* `NAVALUES`

# Modules

* `collections`
* `gridlabd.encoding`
* `gridlabd.framework`
* `gridlabd.resource`
* `gzip`
* `io`
* `os`
* `pandas`
* `sys`
