[[/Utilities/Model]] -- Model editor tool

Syntax: `gridlabd model FILENAME [COMMANDS ...] [OPTIONS ...]`

Options:

* `-s|--save=FILENAME`: save output to FILENAME

Commands:

* `add=PROPERTIES`: add an object

* `class=PATTERN`: define/modify a class

* `delete=PATTERN`: delete object NAME from model

* `get=PATTERN`: get object data

* `list=PATTERN`: list objects

* `modify=PROPERTIES`: modify object data

* `module=PATTERN`: add a module

* `headers=PATTERN`: get header data

* `types=PATTERN`: get data type information

Description:

The model editor utility allow command-line and python-based editing of models.

Patterns are generally of the form `KEY` or `KEY:VALUE` where both `KEY` and
`VALUE` are regular expressions.  Multiple patterns can be provided using
comma separators.

`PROPERTIES` are provided in the form `KEY:VALUE`, where `KEY` is a regular
expression, and multiple properties are comma-separated.

Commands that modify or delete the model will return the old value.

Caveat:

Note that primary patterns must occur only once. For example the following
does not work as expected:

    gridlabd model ieee13.glm modules=power:major,power:minor

because the pattern "power" occurs twice. Only the last instance will be used.
Instead use the following:

    gridlabd model ieee13.glm modules=power:major|minor

Examples:

    gridlabd model ieee13.glm list='Node6[1-4],id:3[23]'
    gridlabd model ieee13.glm get='Node6,GFA.*'
    gridlabd model ieee13.glm get='Node633,class,id'
    gridlabd model ieee13.glm delete=Node633 --save=ieee13.json
    gridlabd model ieee13.glm delete=(from|to):Node633 --save=ieee13_out.json
    gridlabd model ieee13.glm delete=XFMR,(from|to):Node633 --save=ieee13_out.json
    gridlabd model ieee13.glm add=Node14,class:node,bustype:SWING --save=ieee13_out.json
    gridlabd model ieee13.glm modify=Node14,class:substation --save=ieee13_out.json
    



# Classes

## Editor

GLM Model Editor


### `Editor.get() -> None`

Get object properties

Arguments:

* `args`: object name followed by desired properties pattern (default is ".*")

* `kwargs`: Ignored

Returns:

`dict`: object properties


### `Editor.list() -> None`

Generate a list of objects

Arguments:

* `args`: object name refilter patterns (and'ed, default is ".*")

* `kwargs`: property criteria patterns (and'ed, default is ".*")

Returns:

`list`: object names matching criteria


# Functions

## `refilter() -> None`

Filter a list or dict using a RE pattern

Arguments:

* pattern: the RE to use for matching values

* values: the list or dict of values from which matches are drawn

Returns:

* matching values

