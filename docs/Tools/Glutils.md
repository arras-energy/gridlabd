[[/Tools/Glutils]] -- GridLAB-D model access utilities

Syntax: `gridlabd glutils JSONFILE [OPTIONS ...]`

Options:

* `--debug`: enable traceback on exceptions

* `--test`: run a self test

* `graph:VAR`: matrix analysis result

* `node:VAR`: node property vector

* `line:VAR`: line property vector

The `glutils` module is a `gridlabd` runtime model accessor library that can
be used when running Python code in `gridlabd` modules. The accessors allow
Python code to read and write both global variables and object properties.
The library also includes convenience methods to obtain a list global
variables, and dictionaries of object, object header values, classes, class
members, as well as property accessor that can perform unit conversion.

The `glutils` module also includes a JSON model accessor that uses the same
underlying methods as the runtime accessor.

The utilities include a number of useful graph theory methods to extract the
structure and properties of network embedded in the model. Networks are
identified by `from` and `to` properties in edges, or in the case of
`pypower` models, the presence of `fbus` and `tbus` properties that refer to
`bus_i` properties in vertices. The following structural property can be
extracted using the `graph` option:

* `A`: adjacency matrix

* `D`: degree matrix

* `L`: graph Laplacian matrix

* `B`: oriented incidence matrix

* `W`: weighted real Laplacian matrix

* `Wc`: weighted complex Laplacian matrix

All sparse matrices are output in `[[i,j],v]` format. The output can be used
to load sparse matrices using the `scipy.sparse` package.

Metadata arrays are also extract to support interpretation of the graph
matrices. These include the following:

* `lines`: list of line from/to tuples as an index into the `bus` list

* `nodes`: mapping of the node ids as an index into the `branch` list

* `names`: a list of the node and line object names in the model

* `baseMVA`: the baseMVA value, if found

* `row`: the `from` node index in the graph matrices

* `col`: the `to` node index in the graph matrices

* `bus`: the bus list

* `branch`: the branch from/to list

The extraction process automatically generates the edge weights based on the
line impedance. These are stored in `Y`, `Yc`, and `Z`.  All other properties
of lines/branches or nodes/buses can be extracted as a vector using the
`line` and `node` options, respectively by defining the mapping, e.g.,
`node:VAR:PROPERTY`, where `VAR` is any string not already used for graph
matrices and impedance vectors.



# Classes

## GldModel

Dynamic model accessor

The dynamic model accessor allows Python code running in a simulation to access global variables and object properties while the simulation is running.  Use `objects()` to obtain a dict of object names and header values. Use `classes()` to obtain a dict class name and properties. Use `globals()` to obtain a list of global variables.  Use `properties(obj)` to obtain a list of properties of an object. Use `property(obj)` to access an object property or global variable value.


### `GldModel()`

Dynamic model accessor

### `GldModel.classes() -> dict`

Get classes

Returns:

* dict: the classes and property names available


### `GldModel.globals() -> list`

Get list of global names

Returns:

* list: the global variables defined


### `GldModel.objects() -> dict`

Get objects in model

Returns:

* dict: the object names and header values


### `GldModel.properties() -> list`

Get list of properties in object

Returns:

* list: the list of properties defined in an object


### `GldModel.property() -> gld.property`

Get property accessor

Arguments:

* obj (str): object name or global variable name

* name (str): property name (for objects only, None for globals)

Returns:

gld.property: the dynamic property accessor


---

## JsonModel

Static model accessor

### `JsonModel()`

Static model accessor

Arguments:

* jsonfile (str): name of JSON file to access


### `JsonModel.classes() -> dict`

Get classes in model

### `JsonModel.globals() -> list`

Get globals in model

### `JsonModel.objects() -> dict`

Get objects in model

### `JsonModel.properties() -> list`

Get list of object properties

### `JsonModel.property() -> Property`

Get property accessor

Arguments:

* obj (str): object name or global variable name

* name (str): property name (for objects only, None for globals)

Returns:

Property: the property accessor


---

## Network

Network model accessor

Arguments:

* model (dict): JSON model (dynamic model if None)

* matrix (list): List of matrices to generation (all if None)

* nodemap (dict): Map of properties to extract from nodes (or None)

* linemap (dict): Map of properties to extract from lines (or None)

The network model accessor generates a vector for all the extracted
properties in the `nodemap` and `linemap` arguments, if any. The
accessor also generates all the matrices listed in the `matrix`
argument or all if `None`.

Properties generated for `matrix` list:

* last (dt.datetime): time of last update (when force=None)

* lines (list[str]): list of lines in model

* nodes (dict): nodes map

* names (dict): names of node and line objects

* Y (list[float]): list of line admittances

* bus (np.array): bus matrix

* branch (np.array): branch matrix

* row (np.array): row index matrix (branch from values)

* col (np.array): col index matrix (branch to values)

* A (np.array): adjacency matrix

* D (np.array): degree matrix

* L (np.array): graph Laplacian matrix

* B (np.array): oriented incidence matrix

* W (np.array): weighted Laplacian matrix


### `Network(model:dict, matrix:list, nodemap:dict, linemap:dict)`

Network model accessor constructor

### `Network.islands(precision:int) -> int`

Calculate the number of islands in network

Arguments:

* precision (int): the precision with which to evaluate eigenvalues

Returns:

* int: the number of connected subnetworks in the network


### `Network.todict() -> dict`

Get network data as a dict

Arguments:

* extras: include extracted node or line variables with network data

* precision: change precision of extracted values (default is 6)

Returns:

* dict: network data


### `Network.update() -> None`

Update dynamic model

Arguments:

* force (None|bool): force update (None is auto)


---

## Property

JSON property accessor

This property accessor is the static model version of the dynamic accessor that is built-in when running Python inside a GridLAB-D
simulation.


### `Property(model:Model, args:list)`

Property accessor constructor

Arguments:

* model: the GridLAB-D model

* args: global name or object name followed by property name


### `Property.convert_unit(unit:str) -> float`

Convert property units

### `Property.get_initial() -> str | float | int | bool | complex`

Get default value, if any

Returns:
* str|float|int|bool|complex: the default value of the property


### `Property.get_name() -> str`

Get the property name

Returns:

* str: the name of the property


### `Property.get_object() -> str`

Get the object name for this property

Returns:

* str: the name of the object to which this property refers


### `Property.get_value() -> str | float | int | complex | bool | datetime.datetime`

Get value, if any

### `Property.set_object(value:str) -> None`

Set the object name for this property

### `Property.set_value(value:str | float | int | complex | bool | datetime.datetime) -> None`

Set property value

---

## Unit

Unit handling class

### `Unit()`

Unit class constructor

Arguments:

* `unit (str)`: unit specification

Unit objects support arithmetic for units, e.g., addition, subtraction,
multiplication, division, powers, module, and boolean (non-)equality.


### `Unit.matches(x:Union) -> None`

Verifies that two units are compatible for add/subtract operations

Arguments:

* `x (str|Unit)`: unit to check against

* `exception (bool)`: raise exception on mismatch

* `strict (bool)`: match with `None` units fails

Returns:

* `bool`: `True` if matched, otherwise `False`


---

## floatUnit

Float with unit class

The `floatUnit` class supports all floating point arithmetic.


### `floatUnit(value:float | int | str, unit:str | None)`

Float with unit constructor

Arguments:

* `value (float|int|str)`: the floating point value (may include unit if `str`)

* `unit`: unit (if not included in `value`)


### `floatUnit.convert(unit:Union) -> floatUnit`

Convert value to a different unit

Arguments:

* `unit (str|Unit)`: the unit to which the value should be convertor

