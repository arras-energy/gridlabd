[[/Tools/Moutils]] -- Marimo utilities for gridlabd marimo apps


# Classes

## Map

Map rendering class

### `Map(model:*[typing.Union[str, ~io.TextIOWrapper, NoneType]]*, nodedata:*dict*, linkdata:*dict*, options:*dict*)`

Construct map rendering object from model object

Arguments:

* `model`: model object

* `nodedata`: node data extraction dictionary (key is property name
and value is form converter function)

* `linkdata`: link data extraction dictionary (key is property name
and value is form converter function)

Returns:

* `moutils.Map`: map rendering object


### `Map.extract_network(nodedata:*dict*, linkdata:*dict*) -> <I>list</I>`

Extract network data

Arguments:

* `data`: model data

* `nodedata`: node data extraction dictionary (key is property name
and value is form converter function)

* `linkdata`: link data extraction dictionary (key is property name
and value is form converter function)

Returns:

* `list[str]`: list of swing busses (if any)


### `Map.read(data:*dict*, nodedata:*dict*, linkdata:*dict*) -> <I>None</I>`

Read JSON data from model dictionary into model object

Arguments:

* `data`: model data

* `nodedata`: node data extraction dictionary (key is property name
and value is form converter function)

* `linkdata`: link data extraction dictionary (key is property name
and value is form converter function)


### `Map.render() -> <I>marimo.Html</I>`

Render map

Arguments:

* `**options`: `plotly.express.scatter_map` options

Returns:

* `marimo.Html`: marimo Html object


### `Map.save() -> <I>None</I>`

Save a map to a file

Arguments:

* `name`: filename

* `**options`: `plotly.express.scattermap` options


### `Map.show(options:*dict*) -> <I>None</I>`

Show a map in the default web browser

Arguments:

* `**options`: `plotly.express.scattermap` options


# Functions

## `complex_unit(x:<I>str</I>, form:<I>str</I>) -> *complex*`

Convert complex with units

Arguments:

* `x`: complex number

* `form`: desired format

Valid forms:

* `None`: complex number

* `rect`: return complex value in rectangular form (x,y)

* `polar`: return complex value in polar form (mag,arg)

* `i` or `j`: return rectangular form in `i` or `j` format

* `d` or `r`: return polar form in degree or radians

* `real`: return real part

* `imag`: return imaginary part

* `mag`: return magnitude of z

* `arg`: return angle of x in radians

* `ang`: return angle of x in degree

* *other*: return attribute of `x`

Returns:

Returns:

* `complex`: complex value (`form` is `None`)

* `float`: real value (`form` in [`real`,`imag`,`mag`,`ang`,`arg`])

* `tuple`: complex components (`form` in [`rect`,`polar`])

* `str`: formatting complex value (`form` in [`i`,`j`,`d`,`r`])


---

## `float_unit(x:<I>str</I>) -> *float*`

Convert float with units

---

## `gridlabd(args:<I>list</I>, bin:<I>bool</I>, kwargs:<I>dict</I>) -> *subprocess.CompletedProcess*`

Run gridlabd

Arguments:

* `*args`: command line options

* `bin`: enable direct binary runner (faster but disables subcommands and tools)

* `**kwargs`: subprocess run options

Returns:

* `subprocess.CompletedProcess`: process info on success

* `None`: on failure


---

## `model(source:<I>marimo.FileUploadResults</I>, folder:<I>str</I>) -> *None*`

Extract model data

Arguments:

* `source`: marimo upload object

* `folder`: working folder (default is current folder)

Returns:

* `namedtuple`: contents of model dictionary


---

## `render_globals(model:<I>namedtuple</I>, module:<I>dict</I>) -> *marimo.Html*`

Render globals

Arguments:

* `model`: model object

Returns:

* `marimo.Html`: rendered Html object


---

## `render_map(model:<I>namedtuple</I>) -> *marimo.Html*`

Render geodata as map

Arguments:

* `model`: model object

Returns:

* `marimo.Html`: rendered Html object


---

## `render_objects(model:<I>namedtuple</I>) -> *marimo.Html*`

Render objects

Arguments:

* `model`: model object

Returns:

* `marimo.Html`: rendered Html object


---

## `render_sidebar(upload:<I>marimo.FileUploadResults</I>) -> *marimo.Html*`

Render app sidebar

Arguments:

* `upload`: marimo upload object

Returns:

* `marimo.Html`: rendered Html object


---

## `render_status(model:<I>namedtuple</I>) -> *marimo.Html*`

Render status

Arguments:

* `model`: model object

Returns:

* `marimo.Html`: rendered Html object


# Constants


# Modules

* `io`
* `json`
* `marimo`
* `math`
* `os`
* `pandas`
* `plotly.express`
* `plotly.graph_objects`
* `plotly.io`
* `random`
* `subprocess`
