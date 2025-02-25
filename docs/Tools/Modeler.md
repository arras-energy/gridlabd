[[/Tools/Modeler]] -- GridLAB-D JSON file accessor




# Classes

## GridlabdModel

GridLAB-D modeler class implementation

### `GridlabdModel(data:str, name:str, force:bool, initialize:bool)`

Create a gridlabd model object

Arguments:

* `data`: GLM filename, JSON data, or JSON filename

* `name`: filename to use (overrides default filename)

* `force`: force overwrite of existing JSON

* `initialize`: initialize GLM first


### `GridlabdModel.autoname(force:bool) -> str`

Generate a new filename

Arguments:

* `force`: use the first name generate regardless of whether the file
exists

Returns:

* `str`: new filename


### `GridlabdModel.get_objects(as_type:Any) -> Any`

Find objects belonging to specified classes

Arguments:

* `classes`: patterns of class names to search (default is '.*')

* `as_type`: type to use for return value

* `**kwargs`: arguments for as_type

Return:

* `as_type`: object data


### `GridlabdModel.load() -> None`

Load data from dictionary

Arguments:

* `data`: data to load (must be a valid GLM model)


### `GridlabdModel.read_glm(filename:str, force:bool, initialize:bool) -> None`

Read GLM file

Arguments:

* `filename`: name of GLM file to read

* `force`: force overwrite of JSON

* `initialize`: initialize GLM first


### `GridlabdModel.read_json(filename:str) -> None`

Read JSON file

Arguments:

* `filename`: name of JSON file to read


---

## GridlabdModelException

GridLAB-D modeler exception handler

# Constants


# Modules

* `gridlabd.runner`
* `io`
* `json`
* `os`
* `pandas`
* `re`
* `sys`
