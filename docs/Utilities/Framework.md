[[/docs/Utilities/Framework]] -- Tool framework


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

## `double_unit(x:str) -> None`

Convert a string with unit to a float

---

## `gridlabd() -> None`

Simple gridlabd runner

---

## `integer(x:str) -> None`

Convert a string to an integer

---

## `version() -> None`

Get gridlabd version
