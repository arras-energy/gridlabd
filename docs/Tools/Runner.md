[[/Tools/Runner]] -- GridLAB-D runner

Library for gridlabd runner.

Example:

The following python code gets the current version of GridLAB-D.

~~~
import gridlabd.runner as gld
version = gld.gridlabd("--version")
print(version)
~~~



# Classes

## GridlabdRunner

GridLAB-D runner class

### `GridlabdRunner(binary:bool, start:bool, wait:bool, timeout:float, source:Union)`

Construct a runner

Arguments:

* `*args`: gridlabd command line arguments

* `binary`: use the gridlabd binary if possible

* `start`: start gridlabd immediately

* `wait`: wait for gridlabd to complete

* `timeout`: seconds to wait for completion before failing

* `source`: input data source

* `**kwargs`: gridlabd global definitions

Exceptions:

* `GridlabdRunnerException(code,stderr)`


### `GridlabdRunner.is_completed() -> bool`

Check if gridlabd is done

Returns:

* `bool`: process is completed


### `GridlabdRunner.is_running() -> bool`

Check if gridlabd is running

Returns:

* `bool`: gridlabd is running


### `GridlabdRunner.is_started() -> bool`

Check if gridlabd is started

Returns:

* `bool`: gridlabd is started


### `GridlabdRunner.run(timeout:float, source:io.BufferedIOBase) -> None`

Run gridlabd

Arguments:

* `timeout`: seconds to wait before for completion failing

* `source`: input source
Returns:

* `str`: output

Exceptions:

* `GridlabdRunnerException(code,message)`

* `subprocess.TimeoutExpired`


### `GridlabdRunner.start() -> None`

Start gridlabd

Arguments:

* `wait`: enable wait for completion


### `GridlabdRunner.wait() -> None`

Wait for gridlabd to complete

Arguments:

* `timeout`: wait timeout in seconds


---

## GridlabdRunnerException

GridLAB-D runner exception handler

# Functions

## `gridlabd() -> str`

Run gridlabd and return the output

Arguments:

* `*args`: gridlabd command line arguments

* `split`: split output using `split` value (uses `'
'` if `True`)

* `**kwargs`: gridlabd global definitions

Returns:

* `str`: stdout

Exceptions:

* `GridlabdRunnerException(code,stderr)`


# Constants

* `EXITCODES`

# Modules

* `gridlabd`
* `io`
* `json`
* `os`
* `random`
* `shutil`
* `subprocess`
* `sys`
* `time`
