[[/Tools/Framework]] -- Tool framework

The `framework` module contains the infrastructure to support standardized
implementation of tools in GridLAB-D.

Example:

~~~
import framework as app

def main(argv):

    if len(argv) == 1:

        print("
".join([x for x in __doc__.split("
") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    args = read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)
        else:
            error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    return app.E_OK

if __name__ == "__main__":

    try:

        rc = main(sys.argv)
        exit(rc)

    except KeyboardInterrupt:

        exit(app.E_INTERRUPT)

    except Exception as exc:

        if DEBUG:
            raise exc

        if not QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[1]
            print(f"EXCEPTION [{app.EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(app.E_EXCEPTION)
~~~



# Classes

## ApplicationError

Application exception

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

## `double_unit() -> float`

Convert a string with unit to a float

* `x`: string representing real value

Returns:

* real value


---

## `gridlabd() -> Optional`

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

## `read_stdargs() -> list`

Read framework options

Arguments:

* `argv`: the argument list from which to read framework options

Returns:

* Remaining arguments


---

## `version() -> str`

Get gridlabd version

Returns:

* GridLAB-D version info

