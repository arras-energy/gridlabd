"""Location tool

Syntax: gridlabd location [OPTIONS ...]

Options:

* `--debug`: enable debug traceback on exception

* `--quiet`: suppress error messages

* `--silent`: suppress all error messages

* `--warning`: suppress warning messages

* `--verbose`: enable verbose output, if any

* `--system[=LOCATION]`: get/set the default location

* `--find[=LOCATION]`: get location settings
"""

import sys
import framework as app

def main(argv):

    if len(argv) == 1:

        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    args = app.read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        elif key in ["--system"]:

            raise NotImplementedError("TODO")

        elif key in ["--find"]:

            raise NotImplementedError("TODO")

        else:
            error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    return app.E_OK

if __name__ == "__main__":

    try:

        # TODO: development testing -- delete when done writing code
        if not sys.argv[0]:
            sys.argv = [__file__,"--system"]

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

