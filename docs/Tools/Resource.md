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

* `--verbose`: enable verbose output

* `--warning`: disable warning output

Description:

The online resource accessor delivers online resources to GridLAB-D applications.

Valid formats include `json` and `csv` (the default is 'raw').

Examples:

The following command list the properties on the online weather resources

    gridlabd resource --properties=weather

The following command lists the online weather resource index

    gridlabd resource --index=weather

The following command retrieves the online weather data for the specified location

    gridlabd resource --content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3



# Classes

## Resource

Resource class

### `Resource()`

Construct resource object

Arguments:

* `file`: resource file (default is $GLD_ETC/resource.csv)


### `Resource.content() -> None`

Get resource content



### `Resource.index() -> None`

Get resource index (if any)



### `Resource.properties() -> None`

Get resource properties



---

## ResourceError

Resource exception
