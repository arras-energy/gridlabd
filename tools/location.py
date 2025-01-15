"""Location tool

Syntax: `gridlabd location [OPTIONS ...] [FILENAME=KEY[:VALUE][,...] ...]`

Options:

* `--debug`: enable debug traceback on exception

* `--quiet`: suppress error messages

* `--silent`: suppress all error messages

* `--warning`: suppress warning messages

* `--verbose`: enable verbose output, if any

* `--system[=LOCATION]`: get/set the default location

* `--find[=LOCATION]`: get location settings

Description:

The `location` tool allows configuration of the location of a model.

The `location` tool `--system` option is used to setup the system's default
location for models when not location data is not specified in the model.

The `location` tool `--find` options can identify the current location of a
system or a location based on partial information.

The keys and globals handled by the `location` tools include the following:

* `latitude`: the location's latitude

* `longitude`: the location's longitude

* `number`: the location's street number, if any

* `street`: the location's street name

* `zipcode`: the location's postal code

* `city`: the location's city

* `county`: the location's county

* `state`: the location's state

* `region`: the location's region

* `country`: the location's country

Examples:

Get the current location

    gridlabd location --find

Display the default location

    gridlabd location --system

Set the location in a model file

    gridlabd location ieee123.json=country:US,state:CA,county:Kern,city:Bakersfield
"""

import sys
import json
import framework as app
import geocoder

location_keys = ["latitude","longitude","number","street","zipcode","city","county","state","region","country"]

def main(argv):

    if len(argv) == 1:

        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    args = app.read_stdargs(argv)

    def output_raw(data,**kwargs):
        print(data,**kwargs)

    def output_csv(data,**kwargs):
        if isinstance(data,list):
            print("\n".join(data))
        elif isinstance(data,dict):
            print("\n".join([f"{x},{y}" for x,y in data.items()]))
        else:
            raise ResourceError(f"unable to output '{type(data)}' as CSV")

    def output_json(data,**kwargs):
        print(json.dumps(data,**kwargs))

    outputter = output_raw
    outputter_options = {}

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        elif key in ["--format"]:

            if len(value) == 0:

                app.error("missing format")
                return app.E_MISSING

            
            elif value[0] == "csv":

                if len(value) > 1:
                    app.error(f"invalid format options '{','.join(value[1:])}'")
                    return app.E_INVALID
                outputter = output_csv

            elif value[0] == "json":

                options = {x:y for x,y in [z.split(":",1) for z in value[1:]]} if len(value) > 1 else {}
                _bool = lambda x: x=="true" if x in ["true","false"] else None,
                for x,y in {
                    "indent": int,
                    "skipkeys": _bool,
                    "ensure_ascii": _bool,
                    "check_circular": _bool,
                    "allow_nan": _bool,
                    "sort_keys": _bool,
                }.items():
                    try:
                        options[x] = y(options[x])
                    except:
                        pass
                outputter = output_json
                outputter_options = options

        elif key in ["--system"]:

            if not value:

                data = json.loads(app.gridlabd("--globals=json").stdout.decode('utf-8'))
                result = {}
                for item in location_keys:
                    result[item] = data[item]['value'] if item in data else ""

            else:

                raise NotImplementedError("TODO")

        elif key in ["--find"]:

            if not value:

                data = geocoder.ip('me')
                result = {}
                for item in location_keys:
                    result[item] = getattr(data,item) if hasattr(data,item) else ""

            else:

                raise NotImplementedError("TODO")



        else:
            error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    outputter(result,**outputter_options)

    return app.E_OK

if __name__ == "__main__":

    try:

        # TODO: development testing -- delete when done writing code
        if not sys.argv[0]:
            sys.argv = [__file__,"--format=json,indent:4","--find"]

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

