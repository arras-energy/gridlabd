[[/Utilities/Glutils]] -- Utilities to link CVX with GridLAB-D networks


# Classes

## GldModel

Dynamic model accessor

## `GldModel()`

Dynamic model accessor

## `GldModel.classes() -> dict`

Get classes

## `GldModel.globals() -> list`

Get list of global names

## `GldModel.objects() -> dict`

Get objects in model

## `GldModel.properties() -> list`

Get list of properties in object

## `GldModel.property() -> Property`

Get property accessor

Arguments:

* obj (str): object name or global variable name

* name (str): property name (for objects only, None for globals)

Returns:

Property: the property accessor


## JsonModel

Static model accessor

## `JsonModel()`

Static model accessor

Arguments:

* jsonfile (str): name of JSON file to access


## `JsonModel.classes() -> dict`

Get classes in model

## `JsonModel.globals() -> list`

Get globals in model

## `JsonModel.objects() -> dict`

Get objects in model

## `JsonModel.properties() -> list`

Get list of object properties

## `JsonModel.property() -> Property`

Get property accessor

Arguments:

* obj (str): object name or global variable name

* name (str): property name (for objects only, None for globals)

Returns:

Property: the property accessor


## Model

Model accessor base class

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


## `Network(model:dict, matrix:list, nodemap:dict, linemap:dict)`

Network model accessor constructor

## `Network.update() -> None`

Update dynamic model

Arguments:

* force (None|bool): force update (None is auto)


## Property

JSON property accessor

## `Property(model:Model, args:list)`

Property accessor constructor

Arguments:

* model: the GridLAB-D model

* args: global name or object name followed by property name


## `Property.convert_unit(unit:str) -> float`

Convert property units

## `Property.get_initial() -> str | float | int | bool | complex`

Get default value, if any

## `Property.get_name() -> str`

Get property name

## `Property.get_object() -> str`

Get object name

## `Property.get_value() -> str | float | int | complex | bool | datetime.datetime`

Get value, if any

## `Property.rlock() -> None`

Lock property for read

## `Property.set_object(value:str) -> None`

Set object name

## `Property.set_value(value:str | float | int | complex | bool | datetime.datetime) -> None`

Set property value

## `Property.unlock() -> None`

Unlock property

## `Property.wlock() -> None`

Lock property for write

# Functions

## `from_complex(x:str) -> complex`

Convert string complex

## `from_timestamp(x:str) -> dt.datetime`

Convert string to timestamp

## `rarray(x:str) -> np.array`

Convert string to float array
