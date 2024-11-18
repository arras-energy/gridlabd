[[/docs/Utilities/Glunits]] -- Unit support

Syntax: gridlabd glunits VALUE [VALUE OP [...]] [OPTIONS ...]

Options:

* `--unit=[UNIT[,...]]`: units to convert stack when output results

The `glunits` tool support unit arithmetic and unit conversion for shell
scripts and Python applications. All arguments are in RPN, e.g., "2 3 +".
The number of comma-delimited units, if specified, must match the number
of results in the stack.

Examples:

    $ gridlabd glunits "32 degF" --unit=degC
    0 degC

    $ gridlabd glunits "10 m/s^2" "5 lb" x --unit=N
    22.6796 N




# Classes

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

