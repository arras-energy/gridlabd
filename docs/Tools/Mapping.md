[[/Tools/Mapping]] -- Mapping utilities

Syntax: `gridlabd mapping FILENAME [OPTIONS ...]`

Options:

* `--save=FILENAME`: save the image to FILENAME

* `--show[=OPTIONS]`: open the image in a browser using the
  `plotly.scattermap` options

* `-h|--help|help`: output this help to stdout

* `--debug`: enable debug and traceback output on exceptions to stderr

* `--verbose`: enable verbose output to stderr

* `--quiet`: disable error output to stderr

* `--silent`: disable output to stdout

* `--warning`: disable warning output to stderr

Description:

The `mapping` tool generates a map of the network contained in the model
`FILENAME` using `plotly`'s `scattermap` or `scattermapbox` API.  The
configuration file `mapping_config.py` specifies the mapping options
according to the map style selected, e.g., `map` or `mapbox`. The default
mapping configuration is found in the gridlabd shared folder.

Two network modules are currently supported, `powerflow` and `pypower`.
Symbols for various object types and hover popups can be configured in the
mapping configuration file.

Examples:

To generate a map image use the `--save` option, e.g.,

    gridlabd mapping mymodel.json --save=mymodel.png

To open a map in the default browser use the `--show` option, e.g.,

    gridlabd mapping mymodel.json --show

See also:

* [[/Module/Powerflow]]

* [[/Module/Pypower]]

* [Plotly Scattermapbox reference](https://plotly.com/python/reference/scattermapbox/)

* [Plotly Scattermap reference](https://plotly.com/python/reference/scattermap/)




# Classes

## ApplicationError

Application exception

---

## Map

Mapping class

### `Map(model:[<class 'dict'>, <class 'str'>, ~io.TextIOWrapper], nodedata:dict, linkdata:dict)`

Construct a map from a model

Arguments:

* `model`: dict, json file handle, json data

* `nodedata`: data extraction/formatting for node hover

* `linkdata`: data extraction/formatting for link hover

* `options`: plotly scattermap options

See also:

* [[/Module/Powerflow]]

* [[/Module/Pypower]]

* https://plotly.com/python/reference/scattermapbox/

* https://plotly.com/python/reference/scattermap/


### `Map.extract_network(nodedata:dict, linkdata:dict) -> list`

Extract network data

Arguments:

* `nodedata`: nodedata to extract/format

* `linkdata`: linkdata to extract/format

Returns:

* list of swing busses found, if any

See also:

* [[/Module/Powerflow]]

* [[/Module/Pypower]]


### `Map.read(data:dict, nodedata:dict, linkdata:dict) -> None`

Read JSON data

Arguments:

* `data`: the gridlabd model data

* `nodedata`: node data to extract/format

* `linkdata`: link data to extract/format

See also:

* [[/Module/Powerflow]]

* [[/Module/Pypower]]


### `Map.render() -> plotly.graph_objects.Figure`

Render the map

Arguments:

* `options`: plotly scattermap options

Returns:

* plotly figure

See also:

* https://plotly.com/python/reference/scattermapbox/

* https://plotly.com/python/reference/scattermap/


### `Map.save(name:str) -> None`

Save the map in a file

Arguments:

* `options`: plotly render options


### `Map.show() -> None`

Open the map in a browser window

Arguments:

* `options`: plotly render options

See also:

* https://plotly.com/python/reference/scattermapbox/

* https://plotly.com/python/reference/scattermap/


---

## MapError

Mapping exception

# Functions

## `complex_unit() -> None`

Convert complex value with unit

Arguments:

* `form`: formatting (default is None). Valid values are
('i','j','d','r','rect','mag','arg','ang','conjugate','real','imag','unit','str')

* `prec`: precision (default is 2)

* `unit`: unit to convert to (default is None)

Returns:

* `float`: value (if form is 'mag','arg','ang','real','imag')

* `str`: formatted string (if form is 'i','j','d','r','unit','str')

* `tuple[float]`: tuple (if form is 'rect')

* `complex`: complex value (if form is 'conjugate' or None)


---

## `debug() -> None`

Debugging message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are enabled when the `--debug` option is used.


---

## `double_unit() -> float`

Convert a string with unit to a float

* `x`: string representing real value

Returns:

* real value


---

## `error() -> None`

Error message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppressed when the `--quiet` option is used.

If `--debug` is enabled, an exception is raised with a traceback.

If the exit `code` is specified, exit is called with the code.


---

## `exception() -> None`

Exception message output

Arguments:

* `exc`: exception to raise

If `exc` is a string, an `ApplicationError` exception is raised.


---

## `get_options() -> dict`

Extract save/show options from argument value

Arguments:

* `value`: the argument text

* `default`: the default value to use for any options not specified

Returns:

* the option values


---

## `gridlabd() -> Optional`

Simple gridlabd runner

Arguments:

* `args`: argument list

* `bin`: enable direct call to gridlabd binary (bypasses shell and faster)

* `output_to`: run postprocessor on output to stdout

* `kwargs`: options to pass to `subpocess.run`

Returns:

* Complete process object (see `subprocess.CompleteProcess`)

See also:

* https://docs.python.org/3/library/subprocess.html


---

## `integer() -> int`

Convert a string to an integer

* `x`: string representing integer value

Returns:

* integer value


---

## `main() -> int`

Command line processing

Arguments:

* `argv`: command line arguments

Returns:

* exit code


---

## `open_glm() -> io.TextIOWrapper`

Open GLM file as JSON

Arguments:

* `file`: GLM filename

* `tmp`: temporary folder to store JSON file

* `init`: enable model initialization during conversion

* `exception`: enable raising exception instead of returning (None,result)

* `passthru`: enable passing stderr output through to app

Return:

* File handle to JSON file after conversion from GLM


---

## `output() -> None`

General message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppressed when the `--silent` option is used.


---

## `read_stdargs() -> list`

Read framework options

Arguments:

* `argv`: the argument list from which to read framework options

Returns:

* Remaining arguments


---

## `run() -> None`

Run a main function under this app framework

Arguments:

* `main`: the main function to run

* `exit`: the exit function to call (default is `exit`)

* `print`: the print funtion to call on exceptions (default is `print`)

This function does not return. When the app is done it calls exit.


---

## `syntax() -> None`

Print syntax message

Arguments:

* `docs`: the application's __doc__ string

* `print`: the print function to use (default is `print`)

This function does not return. When the function is done it calls exit(E_SYNTAX)


---

## `verbose() -> None`

Verbose message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are enabled when the `--verbose` option is used.


---

## `version() -> str`

Get gridlabd version

Returns:

* GridLAB-D version info


---

## `warning() -> None`

Warning message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppress when the `--warning` option is used.


# Constants

* `DEBUG`
* `E_BADVALUE`
* `E_EXCEPTION`
* `E_FAILED`
* `E_INTERRUPT`
* `E_INVALID`
* `E_MISSING`
* `E_NOTFOUND`
* `E_OK`
* `E_SYNTAX`
* `QUIET`
* `SILENT`
* `VERBOSE`
* `WARNING`

# Modules

* `geocoder`
* `inspect`
* `io`
* `json`
* `math`
* `os`
* `pandas`
* `plotly.express`
* `subprocess`
* `sys`
* `traceback`
* `gridlabd.unitcalc`
