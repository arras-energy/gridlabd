[[/Tools/Framework]] -- Tool framework

The `framework` module contains the infrastructure to support standardized
implementation of tools in GridLAB-D.

Standard options:

The following options are processed by `read_stdargs()`:

* `--debug`: enable debug traceback on exception

* `--quiet`: suppress error messages

* `--silent`: suppress all error messages

* `--warning`: suppress warning messages

* `--verbose`: enable verbose output, if any

Example:

~~~
import gridlabd.framework as app

def main(argv:list[str]) -> int:

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            
            print(__doc__,file=sys.stdout)
            return app.E_OK

        # add your options here

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement your code here

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    app.run(main)
~~~



# Classes

## ApplicationError

Application exception

# Functions

## `complex_unit(x:str, form:str, prec:str, unit:str) -> None`

Convert complex value with unit

Arguments:

* `form`: formatting (default is None). Valid values are
('i','j','d','r','rect','mag','arg','ang','conjugate','real','imag','unit','str')

* `prec`: precision (default is 2)

* `unit`: unit to convert to (default is None)

Returns:

* `float`: value (if form is 'mag','arg','ang','real','imag')

* `str`: formatted string (if form is 'i','j','d','r','unit','str')

* `tuple[float]`: tuple (if form is 'rect')

* `complex`: complex value (if form is 'conjugate' or None)


---

## `debug(msg:list) -> None`

Debugging message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are enabled when the `--debug` option is used.


---

## `double_unit(x:str) -> float`

Convert a string with unit to a float

* `x`: string representing real value

Returns:

* real value


---

## `error(msg:list) -> None`

Error message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppressed when the `--quiet` option is used.

If `--debug` is enabled, an exception is raised with a traceback.

If the exit `code` is specified, exit is called with the code.


---

## `exception() -> None`

Exception message output

Arguments:

* `exc`: exception to raise

If `exc` is a string, an `ApplicationError` exception is raised.


---

## `gridlabd(args:list) -> Optional`

Simple gridlabd runner

Arguments:

* `args`: argument list

* `bin`: enable direct call to gridlabd binary (bypasses shell and faster)

* `output_to`: run postprocessor on output to stdout

* `kwargs`: options to pass to `subpocess.run`

Returns:

* Complete process object (see `subprocess.CompleteProcess`)

See also:

* https://docs.python.org/3/library/subprocess.html


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

* `exception`: enable raising exception instead of returning (None,result)

* `passthru`: enable passing stderr output through to app

Return:

* File handle to JSON file after conversion from GLM


---

## `output(msg:list) -> None`

General message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppressed when the `--silent` option is used.


---

## `read_stdargs(argv:list) -> list`

Read framework options

Arguments:

* `argv`: the argument list from which to read framework options

Returns:

* Remaining arguments


---

## `run(main:callable) -> None`

Run a main function under this app framework

Arguments:

* `main`: the main function to run

* `args`: the main call arguments (defaults to sys.argv)

* `exit`: the exit function to call (default is `exit`)

* `print`: the print funtion to call on exceptions (default is `print`)

This function does not return. When the app is done it calls exit.


---

## `syntax(docs:str) -> None`

Print syntax message

Arguments:

* `docs`: the application's __doc__ string

* `print`: the print function to use (default is `print`)

This function does not return. When the function is done it calls exit(E_SYNTAX)


---

## `test(test:callable, name:str) -> None`

Run module test routine

Arguments:

* `test`: the test function to run

* `name`: name of the app to test

* `exit`: the exit function to call (default is `exit`)

* `print`: the print funtion to call on exceptions (default is `print`)

This function does not return. When the test is done it calls exit.


---

## `verbose(msg:list) -> None`

Verbose message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are enabled when the `--verbose` option is used.


---

## `version(terms:str) -> str`

Get gridlabd version

Returns:

* GridLAB-D version info


---

## `warning(msg:list) -> None`

Warning message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppress when the `--warning` option is used.


# Constants

* `DEBUG`
* `E_BADVALUE`
* `E_EXCEPTION`
* `E_FAILED`
* `E_INTERRUPT`
* `E_INVALID`
* `E_MISSING`
* `E_NOTFOUND`
* `E_OK`
* `E_SYNTAX`
* `QUIET`
* `SILENT`
* `VERBOSE`
* `WARNING`

# Modules

* `geocoder`
* `gridlabd.unitcalc`
* `inspect`
* `io`
* `json`
* `math`
* `os`
* `subprocess`
* `sys`
* `traceback`
