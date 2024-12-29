[[/docs/Utilities/Framework]] -- Tool framework

The `framework` module contains the infrastructure to support standardized
implementation of tools in GridLAB-D.



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

