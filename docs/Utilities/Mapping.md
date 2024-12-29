[[/Utilities/Mapping]] -- Mapping utilities

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



# Classes

## Map

Mapping class

### `Map(model:[<class 'dict'>, <class 'str'>, ~io.TextIOWrapper], nodedata:dict, linkdata:dict)`

Construct a map from a model

Arguments:

* `model`: dict, json file handle, json data

* `nodedata`: data extraction/formatting for node hover

* `linkdata`: data extraction/formatting for link hover

* `options`: plotly scattermap options


### `Map.extract_network(nodedata:dict, linkdata:dict) -> list`

Extract network data

Arguments:

* `nodedata`: nodedata to extract/format

* `linkdata`: linkdata to extract/format

Returns:

* list of swing busses found, if any


### `Map.read(data:dict, nodedata:dict, linkdata:dict) -> None`

Read JSON data

Arguments:

* `data`: the gridlabd model data

* `nodedata`: node data to extract/format

* `linkdata`: link data to extract/format


### `Map.render() -> plotly.graph_objects.Figure`

Render the map

Arguments:

* `options`: plotly scattermap options

Returns:

* plotly figure


### `Map.save(name:str) -> None`

Save the map in a file

Arguments:

* `options`: plotly render options


### `Map.show() -> None`

Open the map in a browser window

Arguments:

* `options`: plotly render options


---

## MapError

Mapping exception

# Functions

## `complex_unit(x:str, form:str, prec:str, unit:str) -> None`

Convert complex value with unit

Arguments:

* `form` (str|None): formatting (default is None). Valid values are
('i','j','d','r','rect','mag','arg','ang','conjugate','real','imag','unit','str')

* `prec` (int): precision (default is 2)

* `unit` (str|None): unit to convert to (default is None)

Returns:

float: value (if form is 'mag','arg','ang','real','imag')

str: formatted string (if form is 'i','j','d','r','unit','str')

tuple[float]: tuple (if form is 'rect')

complex: complex value (if form is 'conjugate' or None)


---

## `double_unit(x:str) -> float`

Convert a string with unit to a float

* `x`: string representing real value

Returns:

* real value


---

## `get_options(value:str, default:dict) -> dict`

Extract save/show options from argument value

Arguments:

* `value`: the argument text

* `default`): the default value to use for any options not specified

Returns:

* the option values


---

## `gridlabd(args:list) -> Optional`

Simple gridlabd runner

Arguments:

* `args`: argument list

* `bin`: enable direct call to gridlabd binary (bypasses shell and faster)

* `kwargs`: options to pass to `subpocess.run`

Returns:

* Complete process object (see `subprocess.CompleteProcess`)

See also:

* [https://docs.python.org/3/library/subprocess.html]


---

## `integer(x:str) -> int`

Convert a string to an integer

* `x`: string representing integer value

Returns:

* integer value


---

## `main(argv:list) -> int`

Command line processing

Arguments:

* `argv`: command line arguments

Returns:

* exit code


---

## `open_glm(file:str, tmp:str, init:bool) -> io.TextIOWrapper`

Open GLM file as JSON

Arguments:

* `file`: GLM filename

* `tmp`: temporary folder to store JSON file

* `init`: enable model initialization during conversion

Return:

* File handle to JSON file after conversion from GLM


---

## `read_stdargs(argv:list) -> list`

Read framework options

Arguments:

* `argv`: the argument list from which to read framework options

Returns:

* Remaining arguments


---

## `version(terms:str) -> str`

Get gridlabd version

Returns:

* GridLAB-D version info

