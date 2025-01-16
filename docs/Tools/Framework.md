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
import framework as app

def main(argv):

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        print("
".join([x for x in __doc__.split("
") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        # TODO: add options here

        else:
            error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # TODO: code implementation here, if any

    return app.E_OK

if __name__ == "__main__":

    try:

        # TODO: development testing -- delete when done writing code
        if not sys.argv[0]:
            sys.argv = ["selftest","--debug"]

        rc = main(sys.argv)
        exit(rc)

    except KeyboardInterrupt:

        exit(app.E_INTERRUPT)

    except Exception as exc:

        if app.DEBUG:
            raise exc

        if not app.QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = app.traceback.TracebackException(e_type,e_value,e_trace).stack[1]
            print(f"EXCEPTION [{app.EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(app.E_EXCEPTION)
~~~



# Functions

## `complex_unit() -> None`

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

## `debug() -> None`

Debugging message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are enabled when the `--debug` option is used.


---

## `double_unit() -> float`

Convert a string with unit to a float

* `x`: string representing real value

Returns:

* real value


---

## `error() -> None`

Error message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppressed when the `--quiet` option is used.


---

## `exception() -> None`

Exception message output

Arguments:

* `exc`: exception to raise


---

## `gridlabd() -> Optional`

Simple gridlabd runner

Arguments:

* `args`: argument list

* `bin`: enable direct call to gridlabd binary (bypasses shell and faster)

* `kwargs`: options to pass to `subpocess.run`

Returns:

* Complete process object (see `subprocess.CompleteProcess`)

See also:

* https://docs.python.org/3/library/subprocess.html


---

## `integer() -> int`

Convert a string to an integer

* `x`: string representing integer value

Returns:

* integer value


---

## `open_glm() -> io.TextIOWrapper`

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

## `output() -> None`

General message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppressed when the `--silent` option is used.


---

## `read_stdargs() -> list`

Read framework options

Arguments:

* `argv`: the argument list from which to read framework options

Returns:

* Remaining arguments


---

## `verbose() -> None`

Verbose message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are enabled when the `--verbose` option is used.


---

## `version() -> str`

Get gridlabd version

Returns:

* GridLAB-D version info


---

## `warning() -> None`

Warning message output

Arguments:

* `msg`: message to output

* `**kwargs`: print options

Messages are suppress when the `--warning` option is used.

