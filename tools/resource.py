"""Online resource accessor

Syntax: `gridlabd resource [OPTIONS ...]`

Options:

* `--content=RESOURCE,INDEX`: download RESOURCE located at INDEX

* `--debug`: enable traceback on exceptions

* `-h|--help|help`: get this help

* `--format=[raw|csv|json]`: output format

* `--index=RESOURCE`: get index for RESOURCE

* `--list[=FORMAT[,OPTIONS[,...]]`: list the available resources

* `--quiet`: suppress error output

* `--properties=RESOURCE`: get a list of resource properties

* `--silent`: support all output exception results

* `--verbose`: enable verbose output

* `--warning`: disable warning output

Description:

The online resource accessor delivers online resources to GridLAB-D applications.

Valid formats include `json` and `csv` (the default is 'raw').

Examples:

The following command list the properties on the online weather resources

    gridlabd resource --properties=weather

The following command lists the online weather resource index

    gridlabd resource --index=weather

The following command retrieves the online weather data for the specified location

    gridlabd resource --content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3
"""

import sys
import os
import io
import json
import pandas as pd
import framework as app
import subprocess
import requests

pd.options.display.max_columns = None
pd.options.display.max_colwidth = None
pd.options.display.width = None

class ResourceError(app.ApplicationError):
    """Resource exception"""

class Resource:
    """Resource class"""
    def __init__(self,file=None):
        """Construct resource object

        Arguments:

        * `file`: resource file (default is $GLD_ETC/resource.csv)
        """
        # default file is from GLD_ETC
        if not file and "GLD_ETC" in os.environ:
            file = os.path.join(os.environ["GLD_ETC"],"resource.csv")
            if not os.path.exists(file):
                file = None

        # load data
        self.data = pd.read_csv(file,
            index_col=0,
            na_filter=False,
            )

        # get globals from gridlabd
        self.globals = app.gridlabd("--globals=json",
            output_to=lambda x:{y:z['value'] for y,z in json.loads(x).items()},
            )
        location = app.location()
        if location:
            self.globals.update(**location)
        else:
            app.warning("unable to get location from app")
        self.globals["repository"] = "gridlabd"
        self.globals["branch"] = self.globals["version.branch"]
        self.request = None

    def _download(self,protocol,hostname,port,path,output_to=lambda x:x):
        url = f"{protocol}://{hostname}:{port}{path}"
        req = requests.get(url)
        self.request = req
        self.request.url = url
        if req.status_code == 200:
            return output_to(req.content.decode("utf-8"))
        else:
            return None

    def properties(self,passthru='*',**kwargs):
        """Get resource properties

        """
        if not kwargs["name"] in self.data.index:
            raise ResourceError(f"'{kwargs['name']}' not found")
        result = {"resource":kwargs["name"]}
        for key,value in dict(zip(self.data.columns,self.data.loc[kwargs['name']].tolist())).items():
            try:
                result[key] = value.format(**kwargs,**self.globals) if type(value) is str else value
            except KeyError:
                e_value = str(sys.exc_info()[1]).strip("'")
                if e_value in passthru or passthru == '*':
                    args = {str(e_value):f"{{{e_value}}}"}
                    return self.properties(**args,**kwargs)
                raise
        return result

    def index(self,**kwargs):
        """Get resource index (if any)

        """
        spec = self.properties(passthru=['index'],**kwargs)

        if not spec['index']:

            raise ResourceError(f"{spec['resource']} has no index")

        return self._download(spec['protocol'],spec['hostname'],spec['port'],spec['index'],
            output_to=lambda x:x.strip().split("\n"))

    def content(self,**kwargs):
        """Get resource content

        """
        spec = self.properties(**kwargs)

        if not spec['content']:

            raise ResourceError(f"{spec['resource']} has not content")

        return self._download(spec['protocol'],spec['hostname'],spec['port'],spec['content'])

def main(argv):

    if len(argv) == 1:

        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    args = app.read_stdargs(argv)
    
    resources = Resource()

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
            return app.E_OK
        
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

            else:

                app.error(f"invalid output format '{value[0]}'")
                return app.E_INVALID

        elif key in ["--list"]:

            outputter(resources.data.index.tolist(),**outputter_options)
            return app.E_OK

        elif key in ["--properties"]:

            options = value[1:] if len(value) > 1 else []
            value = value[0] if len(value) > 0 else None
            if len(options) > 0:
                raise ResourceError(f"invalid option '{options[0]}")
                return E_INVALID
            if value:
                if not value in resources.data.index:
                    app.error(f"'{item}' is not a valid resource name")
                    return app.E_NOTFOUND
                data = resources.properties(name=value)
            else:
                data = resources.data.columns.tolist()
            outputter(data,**outputter_options)
            return app.E_OK

        elif key in ["--index"]:
            if not value:
                app.error("missing resource name")
                return E_MISSING
            for item in value: # TODO only one allowed
                if not item in resources.data.index:
                    app.error(f"'{item}' is not a valid resource name")
                    return app.E_NOTFOUND
                outputter(resources.index(name=item),**outputter_options)
            return app.E_OK
        
        elif key in ["--content"]:
            
            if len(value) == 0:
                app.error("missing resource name")
                return app.E_MISSING
            index = resources.index(name=value[0])

            if len(value) == 1:
                app.error("missing index value")
                return app.E_MISSING
            source = value[1]

            options = value[2:] if len(value) > 1 else {}

            if not source in index:
                app.error(f"'{source}' is not found in '{value[0]}' index ")
                return app.E_NOTFOUND

            result = resources.content(name=value[0],index=source)
            if result:
                outputter(result,**outputter_options)
            else:
                app.error(f"{resources.request.url}: {resources.request.content.decode('utf-8')}")
                return E_FAILED
            return app.E_OK

        else:
            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID



    return app.E_OK

if __name__ == "__main__":

    # local development test
    # TODO: remove this block when done developint
    if not sys.argv[0]:

        # sys.argv.extend(["--list"])
        # sys.argv.extend(["--format=csv","--list"])
        # sys.argv.extend(["--format=json","--list"])
        # sys.argv.extend(["--format=json,indent:4","--list"])

        # sys.argv.extend(["--index"]) # should be an error
        # sys.argv.extend(["--index=weather"])
        # sys.argv.extend(["--format=json","--index=weather"])
        # sys.argv.extend(["--format=json,indent:4","--index=weather"])

        # sys.argv.extend(["--properties"])
        # sys.argv.extend(["--properties=weather"])
        # sys.argv.extend(["--debug","--format=json,indent:4","--properties=weather"])

        # sys.argv.extend(["--content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3,csv"])
        # sys.argv.extend(["--format=csv","--content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3,csv"])
        # sys.argv.extend(["--format=json","--content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3,csv"])

        # sys.argv.extend(["--index=localhost"]) # should be an error
        # sys.argv.extend(["--content=localhost"]) # should be an error
        # sys.argv.extend(["--content=junk"]) # should be an error

        pass

    try:

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
