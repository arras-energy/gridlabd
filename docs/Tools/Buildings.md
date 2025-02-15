[[/Tools/Buildings]] -- Buildings

Syntax: gridlabd buildings [OPTIONS ...]

Options:

* `-C|--county=COUNTRY/STATE/COUNTY`: download county-level data

* `-L|--locate`: include latitude and longitude

* `-A|--address: include address (warning: this can take a long time to process)

* `-o|--output=FILENAME`: output to a file

* `--nocache`: do not use cache data

* `--cleancache`: clean cache data



# Classes

## Buildings

Buildings data

### `Buildings(country:str, state:str, county:str, locate:bool, address:bool, cache:[bool | str])`

Construct buildings object

Arguments:

* `country`: specifies the country

* `state`: specify the state, province, or region)

* `county`: specify the county

* `locate`: enable addition of latitude and longitude data

* `address`: enable addition of address data (can be very slow)

* `cache`: control cache (use 'clean' to refresh cache data)


---

## BuildingsError

Buildings exception

---

## Resource

Resource class

### `Resource()`

Construct resource object

Arguments:

* `file`: resource file (default is `$GLD_ETC/resource.csv`)


### `Resource.content() -> str`

Get resource content

Arguments:

* `name`: resource name

* `index`: resource index

* `**kwargs`: options (see `properties()`)

Returns:

* `str`: Resource contents


### `Resource.headers() -> Union`

Get resource header

* `name`: resource name

* `index`: resource index

* `**kwargs`: options (see `properties()`)

Returns:

* `str`: header content if a simple string

* `list`: header content if a list

* `dict`: header contents if a dict


### `Resource.index(kwargs:dict) -> Union`

Get resource index (if any)

Arguments:

* `kwargs`: property keys to collect

Returns:

* `str`: a single index value

* `list`: a list of index values

* `dict`: a dict of index values


### `Resource.list(pattern:str) -> list`

Get a list of available resources

Arguments:

* `pattern`: regular expression for resource names to be returned


### `Resource.properties(passthru:str, kwargs:dict) -> dict`

Get resource properties

Arguments:

* `passthru`: resource keys that are passed through if not resolved

* `kwargs`: keys to include in resolving properties

Returns:

`dict`: resolved properties

Description:

The following keys are commonly found in resource properties:

* `index`: the resource index

* `origin`: the resource origin on github, e.g. `{organization}/{repo}`

* `organization`: the github organization

* `gitbranch`: the resource branch on github


# Functions

## `geocode() -> None`


Decode geohash, returning two float with latitude and longitude
containing only relevant digits and with trailing zeroes removed.

