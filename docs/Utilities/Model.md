[[/Utilities/Model]] -- Model editor tool

Syntax: `gridlabd model FILENAME [COMMANDS ...] [OPTIONS ...]`

Options:

* `-s|--save=FILENAME`: save output to `FILENAME`

Commands:

* `add=NAME,PROPERTY:VALUE[,...]`: add an object

* `delete=PATTERN[,PROPERTY:VALUE]`: delete objects

* `get=PATTERN[,PROPERTY:VALUE`: get object data

* `globals=[PATTERN|NAME][,PROPERTY:VALUE]`: get/set globals

* `copy=PATTERN[,PROPERTY:VALUE]`: copy objects 

* `list=PATTERN[,PROPERTY:VALUE]`: list objects

* `modify=PATTERN,PROPERTY:VALUE[,...]`: modify object data

* `move=PATTERN[,PROPERTY:VALUE]`: move objects 

Description:

The model editor utility allows command-line and python-based editing of models.

`PATTERN` is a regular expression used to match objects or global variable
names. `PROPERTY` and `VALUE` can be regular expressions or a property name
and value tuple for get or set operations, respectively. When comma-separated
patterns are allowed, they are interpreted as `and` operations. Note that the
`add` command does not use regular expressions for `NAME`, which are
interpreted literally.

Commands that modify or delete objects or data will output the old value
(s). Output is always generated to `stdout` as a CSV table with property
names in the header row.

The save `FILENAME` format is limited to JSON.

Caveat:

The model editor does not check whether the action will result in a faulty
model, e.g., deleting a node that is referened by a link, adding a property that
is not valid for the class, or changing an object property to something invalid.

Examples:

    gridlabd model ieee13.glm list='Node6[1-4],id:3[23]'
    gridlabd model ieee13.glm get='Node6,GFA.*'
    gridlabd model ieee13.glm get='Node633,class,id'
    gridlabd model ieee13.glm delete=Node633 --save=ieee13.json
    gridlabd model ieee13.glm delete=(from|to):Node633 --save=ieee13_out.json
    gridlabd model ieee13.glm delete=XFMR,(from|to):Node633 --save=ieee13_out.json
    gridlabd model ieee13.glm add=Node14,class:node,bustype:SWING --save=ieee13_out.json
    gridlabd model ieee13.glm modify=Node633,class:substation --save=ieee13_out.json
    



# Classes

## Editor

GLM Model Editor


### `Editor.add() -> None`

Add objects

Arguments:

* `args`: object name pattern followed by desired properties patterns (if any)

* `kwargs`: key and value patterns to match properties

Returns:

`dict`: object properties added


### `Editor.delete() -> None`

Delete objects

Arguments:

* `args`: object name pattern followed by desired properties patterns (if any)

* `kwargs`: key and value patterns to match properties

Returns:

`dict`: deleted object properties


### `Editor.get() -> None`

Get object properties

Arguments:

* `args`: object name pattern followed by desired properties patterns (if any)

* `kwargs`: key and value patterns to match properties

Returns:

`dict`: object properties


### `Editor.globals() -> None`

Read/write globals

Arguments:

* `args`: globals name pattern followed by desired properties patterns (if any)

* `kwargs`: key and value patterns to get/set globals

Returns:

`dict`: global properties added


### `Editor.list() -> None`

Generate a list of objects

Arguments:

* `args`: object name patterns (and'ed, default is ".*")

* `kwargs`: property criteria patterns (and'ed, default is ".*")

Returns:

`list`: object names matching criteria


### `Editor.modify() -> None`

Modify object properties

Arguments:

* `args`: object name pattern followed by desired properties patterns (if any)

* `kwargs`: key and value patterns to match properties

Returns:

`dict`: object properties prior to modification

