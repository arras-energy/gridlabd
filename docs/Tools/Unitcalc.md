[[/Tools/Unitcalc]] -- Unit support

Syntax: gridlabd unitcalc VALUE [VALUE OP [...]] [OPTIONS ...]

Options:

* `--unit=[UNIT[,...]]`: units to convert stack when output results

* `help`: display this help

* `list`: list of primitives in unit dictionary

* `test`: perform self-test

The `unitcalc` tool support unit arithmetic and unit conversion for shell
scripts and Python applications. All arguments are in RPN, e.g., "2 3 +". 

The number of comma-delimited units, if specified, must match the number of
results in the stack.

Values may be provided with or without units. Values without units are
considered compatible with values that have using, i.e., the same unit for
summation and scalars for products.  Units must always be provided with a
space separating the number from the unit.

It is important to know that composite units are calculated as needed from
primitive units, e.g., although `m/s` is not listed, it is supported.

Supported operators include the following:

* `+`, `add`, `sum`: addition

* `-`, `sub`, `subtract`,`minus`: subtraction

* `*`, `x`, `mul`, `multiply`, `prod`, `product`: multiplication

* `/`, `div`, `divide``: division

* `//`, `quo`, `quotient`, `floordiv`, `fdiv`: floor division (quotient)

* `%`, `mod`, `modulo`, `rem`, `remainder`: modulo (remainder)

* `^`, `**`, `pow`, `power`: power

The following stack operations are also supported:

* `copy`: copy the head item

* `pop`:

* `rol`: rotate stack left

* `ror`: rotate stack right

* `rev`: reverse stack

* `swap`, `exchange`: swap the top two stack items

Examples:

    $ gridlabd unitcalc "32 degF" --unit=degC
    0 degC

    $ gridlabd unitcalc "32.2 ft/s^2" "5 lb" x --unit=N
    22.2591 N




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


# Constants

* `SCALARS`
* `SPECS`
* `TAGS`
* `UNITS`

# Modules

* `copy`
* `math`
* `os`
* `re`
* `sys`
