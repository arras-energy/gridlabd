[[/Tools/Weather]] -- Access weather data from NREL

Syntax: gridlabd weather COUNTRY STATE COUNTY [OPTIONS ...]

Options:

* `--model[=GLMFILE]`: enable model GLM output (default is to
  `{COUNTRY}_{STATE}_{COUNTY}_{TYPE}.glm`) 

* `--player[=CSVFILE]`: enable player CSV output (default is to 
  `{COUNTRY}_{STATE}_{COUNTY}_{TYPE}.csv`) 

* `--type=TYPE`: specify the type of weather data to download

* `--start`: set the start date (default is `2018-01-01 00:00:00 EST`)

* `--end`: set the end date (default is `2019-01-01 00:00:00 EST`)

Description:

The `weather` tool downloads weather data from the NREL building stock data
respositories. This weather data is used for building energy modeling, but
can also be used for other purposes in GridLAB-D.

The only COUNTRY supported now is `US`. Valid STATE and COUNTY values can be obtained
from the `census` tool.

The follow weather TYPE values are supported:

* `tmy3`: typical meteorological data from NREL that corresponds to enduse load data (see `enduse` tool)

* `amy2018`: actual meteorological data from NREL that corresponds to enduse load data (see `enduse` tool)

Example:

The following example create a typical weather model for December 2020 in Snohomish County Washington 

~~~
gridlabd weather US WA Snohomish --player --model -type=tmy3 --start='2020-12-01 00:00:00-08:00' --end='2021-01-01 00:00:00-08:00'
~~~

See also:

* [[/Tools/Census]]
* [[/Toosl/Enduse]]
* [[/Tools/Framework]]



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
