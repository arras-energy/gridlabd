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

* `--silent`: suppress all output exception results

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

    TIMEOUT = 5

    def __init__(self,file=None):
        """Construct resource object

        Arguments:

        * `file`: resource file (default is $GLD_ETC/resource.csv)
        """

        # default file is from GLD_ETC
        if os.path.exists("../runtime/resource.csv"):
            file = "../runtime/resource.csv"
        elif not file and "GLD_ETC" in os.environ:
            file = os.path.join(os.environ["GLD_ETC"],"resource.csv")
            if not os.path.exists(file):
                file = None

        # load data
        self.data = pd.read_csv(file,
            index_col=0,
            na_filter=False,
            comment="#",
            ).to_dict('index')
        # print(self.data)

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

    def _download(self,
            protocol,port,hostname,content,
            output_to=lambda x:x,headers={},
            **kwargs):
        url = f"{protocol}://{hostname}:{port}{content}"
        print(url)
        try:
            req = requests.get(url,headers=headers,timeout=self.TIMEOUT)
            req.raise_for_status()
        except Exception as err:
            raise err from err
        self.request = req
        self.request.url = url
        app.debug(f"downloading '{url}' with headers={req.request.headers}")
        return output_to(req.content.decode("utf-8"))

    def _headers(self,
            protocol,port,hostname,content,
            output_to=lambda x:x,headers={},
            **kwargs):
        url = f"{protocol}://{hostname}:{port}{content}"
        print(url)
        try:
            req = requests.head(url,headers=headers,timeout=self.TIMEOUT)
            req.raise_for_status()
        except Exception as err:
            raise err from err
        self.request = req
        self.request.url = url
        app.debug(f"downloading '{url}' with headers={req.request.headers}")
        return output_to(req.headers)

    def properties(self,passthru='*',**kwargs):
        """Get resource properties

        """
        name = kwargs['name']
        if not name in self.data:
            raise ResourceError(f"'{name}' not found")
        result = {"resource":name}
        for key,value in self.data[name].items():
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
        if not 'passthru' in kwargs:
            kwargs['passthru'] = '*'
        spec = self.properties(**kwargs)

        if not spec['index']:

            raise ResourceError(f"{spec['resource']} has no index")

        spec['content'] = spec['index']
        del spec['index']

        return self._download(
            headers={'Accept':'text/plain'},
            output_to=lambda x:x.strip().split("\n"),
            **spec)

    def headers(self,**kwargs):
        """Get resource header

        """
        if not 'passthru' in kwargs:
            kwargs['passthru'] = '*'
        spec = self.properties(**kwargs)

        if not spec['content']:

            raise ResourceError(f"{spec['resource']} has no content")

        return self._headers(
            headers = {
                'Accept': spec['mimetype'] if spec['mimetype'] else '*/*',
                'Connection': 'close',
                },
            **spec)

    def content(self,**kwargs):
        """Get resource content

        """
        if not 'passthru' in kwargs:
            kwargs['passthru'] = '*'
        spec = self.properties(**kwargs)

        if not spec['content']:

            raise ResourceError(f"{spec['resource']} has not content")

        return self._download(
            headers = {
                'Accept': spec['mimetype'] if spec['mimetype'] else '*/*',
                'Connection': 'close',
                },
            **spec)

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
        elif isinstance(data,str):
            data = pd.read_csv(io.StringIO(data),dtype=str)
            print(data.to_csv())
        else:
            raise ResourceError(f"unable to output '{type(data)}' as CSV")

    def output_json(data,**kwargs):
        if isinstance(data,str):
            data = pd.read_csv(io.StringIO(data),dtype=str)
            print(data.to_json(indent=2))
        else:
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

    # local development tests
    # TODO: comment this block entire when done developing
    if not sys.argv[0]:

        #
        # Test library functions (comprehensive scan of all contents)
        #
        TESTLIST = [] # None => all resources
        resource = Resource()
        for name in resource.data if TESTLIST is None else TESTLIST:
            print(f"*** {name} ***")
            print("Properties:")
            for key,value in resource.properties(name=name).items():
                print(f"  {key}: {repr(value)}")
            try:
                index = resource.index(name=name)
                if index:
                    for item in index:
                        content = resource.headers(name=name,index=item)
                        print(f"{name}/{item}... {content['content-length']} bytes",flush=True)
            except ResourceError as err:
                print(f"{name}... {err}")


        #
        # Test command line options (e.g., one at a time)
        #

        # options = ["--debug","--format=csv"]
        # options = ["--debug","--format=json,indent:4"]
        # sys.argv.extend(["--list"])
        # sys.argv.extend([*options,"--list"])

        # sys.argv.extend([*options,"--index"]) # should be an error
        # sys.argv.extend([*options,"--index=weather"])

        # sys.argv.extend([*options,"--properties"])
        # sys.argv.extend([*options,"--properties=weather"])

        # sys.argv.extend([*options,"--content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3,csv"])

        # sys.argv.extend([*options,"--index=localhost"]) # should be an error
        # sys.argv.extend([*options,"--content=localhost"]) # should be an error
        # sys.argv.extend([*options,"--content=junk"]) # should be an error

        print("Tests completed")
        quit(0)

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
