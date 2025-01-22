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

* `file`: resource file (default is $GLD_ETC/resource.csv)


### `Resource.content(kwargs:dict) -> str`

Get resource content

Arguments:

* `**kwargs`: options (see `properties()`)

Returns:

* Resource contents


### `Resource.headers(kwargs:dict) -> Union`

Get resource header



### `Resource.index(kwargs:dict) -> Union`

Get resource index (if any)



### `Resource.list(pattern:str) -> list`

Get a list of available resources

Argument


### `Resource.properties(passthru:str, kwargs:dict) -> dict`

Get resource properties



---

## ResourceError

Resource exception

# Functions

## `main() -> int`

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

