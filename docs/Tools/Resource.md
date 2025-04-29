[[/Tools/Resource]] -- Online resource accessor

Syntax: `gridlabd resource [OPTIONS ...]`

Options:

* `--content=RESOURCE,INDEX`: download RESOURCE located at INDEX

* `--debug`: enable traceback on exceptions

* `-h|--help|help`: get this help

* `--format=[raw|csv|json]`: output format

* `--index=RESOURCE`: get index for RESOURCE

* `--list[=FORMAT[,OPTIONS[,...]]`: list the available resources

* `--quiet`: suppress error output

* `--properties=RESOURCE`: get a list of resource properties

* `--silent`: suppress all output exception results

* `--test[=PATTERN]`: test resources matching pattern (default is '.*')

* `--verbose`: enable verbose output

* `--warning`: disable warning output

Description:

The online resource accessor delivers online resources to GridLAB-D applications.

Valid formats include `json` and `csv` (the default is 'raw').

Examples:

The following command lists the released versions

    gridlabd resource --index=version

The following command lists the properties on the online weather resources

    gridlabd resource --properties=weather

The following command retrieves the online weather data for the specified location

    gridlabd resource --content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3



# Classes

## Resource

Resource class

### `Resource()`

Construct resource object

Arguments:

* `file`: resource file (default is `$GLD_ETC/resource.csv`)


### `Resource.cache(name:str, index:str) -> str`

Get local cache filename for resource

Arguments:

* `name`: name of resource

* `index`: index of file in resource

* `freshen`: method of refreshing the cache
(`None`=never, `False`=always, `True`=updated)

* `**kwargs`: override(s) of gridlabd globals
Returns:

* `str`: filename of local cache copy of resource content


### `Resource.content() -> str`

Get resource content

Arguments:

* `name`: resource name

* `index`: resource index

* `**kwargs`: options (see `properties()`)

Returns:

* `str`: Resource contents


### `Resource.dataframe(options:dict) -> pandas.DataFrame`

Get resource dataframe

Arguments:

* `name`: resource name

* `index`: resource index

* `**kwargs`: options (see `properties()`)

* `options`: options (see `pandas.read_csv()`)

Returns:

* `pandas.DataFrame`: Resource contents


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


---

## ResourceError

Resource exception

# Functions

## `main(argv:list) -> int`

Resource tool main routine

Arguments:

* `argv`: command line arguments

Returns:

* Exit code


---

## `test() -> None`

Run tests on resources that match the specified pattern

Arguments:

* `pattern`: the resource name as a regular expression

Returns:

* Exit code: E_OK on success, E_FAILED on failure


# Constants


# Modules

* `PIL.Image`
* `gridlabd.framework`
* `gridlabd.runner`
* `io`
* `json`
* `numpy`
* `os`
* `pandas`
* `re`
* `requests`
* `subprocess`
* `sys`
