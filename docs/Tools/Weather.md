[[/Tools/Weather]] -- Access weather data from NREL

Syntax: gridlabd weather COUNTRY STATE COUNTY TYPE [OPTIONS ...]

Options:

Description:

The `weather` tool downloads weather data from the NREL building stock data
respositories. This weather data is used for building energy modeling, but
can also be used for other purposes in GridLAB-D.

The only COUNTRY supported now is `US`.  The 


Example:




# Classes

## Weather

Weather class

### `Weather(country:str, state:str, county:str | None, weather_type:str, timestep:str | None, ignore_errors:bool)`

Access weather data

Arguments:

* `country`: country code (e.g., "US")

* `state`: state abbreviation (e.g., "CA")

* `county`: County name pattern (must by unique)

* `weather_type`: Specify type of weather data to download. Valid
values are `tmy3` and `amy2018`.

* `timestep`: timeseries aggregate timestep (default '1h')

* `ignore_errors`: ignore download errors


### `Weather.to_glm(glmname:str, glmdata:dict) -> None`

Write GLM objects created by players

### `Weather.to_player(csvname:str) -> dict`

Write player data

Argument:

* `csvname`: name of CSV file

Returns:

* `dict`: GLM objects needed to access players


---

## WeatherError

Weather exception

# Functions

## `main(argv:list) -> int`

Weather main routine

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

* `WEATHER_COLUMNS`
* `WEATHER_URL`

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
