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

* `--test[=PATTERN]`: test resources matching pattern (default is '.*')

* `--verbose`: enable verbose output

* `--warning`: disable warning output

Description:

The online resource accessor delivers online resources to GridLAB-D applications.

Valid formats include `json` and `csv` (the default is 'raw').

Examples:

The following command lists the released versions

    gridlabd resource --index=version

The following command lists the properties on the online weather resources

    gridlabd resource --properties=weather

The following command retrieves the online weather data for the specified location

    gridlabd resource --content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3
"""

import sys
import os
import io
import json
import re
import pandas as pd
import gridlabd.framework as app
import subprocess
import requests
from typing import TypeVar, Union
from PIL import Image
import numpy as np

pd.options.display.max_columns = None
pd.options.display.max_colwidth = None
pd.options.display.width = None

class ResourceError(app.ApplicationError):
    """Resource exception"""

class Resource:
    """Resource class"""

    TIMEOUT = 5
    PROPERTIES = []

    mimetypes = {
        ".csv.gz" : lambda x: pd.read_csv(io.BytesIO(x.content),compression="gzip",low_memory=False),
        ".csv" : lambda x: pd.read_csv(io.StringIO(x.content.decode("utf-8")),low_memory=False),
        ".json" : lambda x: json.load(io.StringIO(x.content.decode("utf-8"))),
        ".tif" : lambda x: np.array(Image.open(io.BytesIO(x.content))),
        ".png" : lambda x: np.array(Image.open(io.BytesIO(x.content))),
        ".tmy3" : lambda x: pd.read_csv(io.StringIO(x.content.decode("utf-8")),
                low_memory=False,
                skiprows=1,
                header=[0],
                index_col=[0],
                parse_dates=[[0,1]],
                ),
    }

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
            )
        self.PROPERTIES = list(self.data.columns)
        self.data = self.data.to_dict('index')

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
        try:
            app.verbose(f"requests.get(url={repr(url)},headers={headers},timeout={self.TIMEOUT})")
            req = requests.get(url,headers=headers,timeout=self.TIMEOUT)
            req.raise_for_status()
        except Exception as err:
            raise err from err
        self.request = req
        self.request.url = url
        app.debug(f"downloading '{url}' with headers={req.request.headers}")
        for mimetype,process in self.mimetypes.items():
            if content.endswith(mimetype):
                return process(req)
        return output_to(req.content.decode("utf-8"))

    def _headers(self,
            protocol,port,hostname,content,
            output_to=lambda x:x,headers={},
            **kwargs):
        url = f"{protocol}://{hostname}:{port}{content}"
        try:
            app.verbose(f"requests.head(url={repr(url)},headers={headers},timeout={self.TIMEOUT})")
            req = requests.head(url,headers=headers,timeout=self.TIMEOUT)
            req.raise_for_status()
        except Exception as err:
            raise err from err
        self.request = req
        self.request.url = url
        app.debug(f"downloading '{url}' with headers={req.request.headers}")
        return output_to(req.headers)

    def list(self,pattern:str='.*') -> list[str]:
        """Get a list of available resources

        Argument
        """
        return sorted([x for x in self.data if re.match(pattern,x)])

    def properties(self,passthru:str='*',**kwargs:dict) -> dict:
        """Get resource properties

        """
        name = kwargs['name']
        if not name in self.list():
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

    def index(self,**kwargs:dict) -> Union[str,list,dict]:
        """Get resource index (if any)

        """
        if not 'passthru' in kwargs:
            kwargs['passthru'] = '*'
        spec = self.properties(**kwargs)

        if not spec['index']:

            raise ResourceError(f"{spec['resource']} has no index")

        spec['content'] = spec['index']
        del spec['index']

        if "@" in spec['content']:
            spec['content'],key = spec['content'].split("@",1)
            mimetype = "application/json"
            output_as = lambda x: [y[key] for y in json.loads(x)]
        else:
            mimetype = "text/plain"
            output_as = lambda x: x.strip().split("\n")


        return self._download(
            headers={
                'Accept':mimetype,
                'Cache-Control':'no-cache',
                },
            output_to=output_as,
            **spec)

    def headers(self,**kwargs:dict) -> Union[str,list,dict]:
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
                'Cache-Control':'no-cache',
                },
            **spec)

    def content(self,**kwargs:dict) -> str:
        """Get resource content

        Arguments:

        * `**kwargs`: options (see `properties()`)

        Returns:

        * Resource contents
        """
        if not 'passthru' in kwargs:
            kwargs['passthru'] = '*'
        spec = self.properties(**kwargs)

        if not spec['content']:

            raise ResourceError(f"{spec['resource']} has no content")

        return self._download(
            headers = {
                'Accept': spec['mimetype'] if spec['mimetype'] else '*/*',
                'Connection': 'close',
                },
            **spec)

def main(argv:list) -> int:
    """Resource tool main routine

    Arguments:

    * `argv`: command line arguments

    Returns:

    * Exit code
    """
    if len(argv) == 1:

        app.syntax(__doc__)

    args = app.read_stdargs(argv)
    
    resources = Resource()

    def output_raw(data,**kwargs):
        if isinstance(data,np.ndarray):
            print(data.tolist(),**kwargs)
        else:
            print(data,**kwargs)

    def output_csv(data,**kwargs):
        if isinstance(data,list):
            print("\n".join(data))
        elif isinstance(data,dict):
            print("\n".join([f"{x},{y}" for x,y in data.items()]))
        elif isinstance(data,str):
            data = pd.read_csv(io.StringIO(data),dtype=str)
            print(data.to_csv(**kwargs))
        elif isinstance(data,pd.DataFrame):
            print(data.to_csv(**kwargs))
        elif isinstance(data,np.ndarray):
            print(np.savetxt("/dev/stdout",data,**kwargs))
        else:
            raise ResourceError(f"unable to output '{type(data)}' as CSV")

    def output_json(data,**kwargs):
        if isinstance(data,str):
            data = pd.read_csv(io.StringIO(data),dtype=str)
            print(data.to_json(indent=2))
        elif isinstance(data,pd.DataFrame):
            print(data.to_json(**kwargs))
        elif isinstance(data,np.ndarray):
            print(json.dumps(data.tolist(),**kwargs))
        else:
            print(json.dumps(data,**kwargs))

    outputter = output_raw
    outputter_options = {}

    for key,value in args:

        if key in ["-h","--help","help"]:

            print(__doc__)
            return app.E_OK
        
        elif key in ["--format"]:

            if len(value) == 0:

                app.error("missing format")
                return app.E_MISSING

            
            elif value[0] == "csv":

                # if len(value) > 1:
                #     app.error(f"invalid format options '{','.join(value[1:])}'")
                #     return app.E_INVALID
                outputter_options = {x:y for x,y in [z.split(":",1) for z in value[1:]]} if len(value) > 1 else {}
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

            outputter(resources.list(*value),**outputter_options)
            return app.E_OK

        elif key in ["--properties"]:

            options = value[1:] if len(value) > 1 else []
            value = value[0] if len(value) > 0 else None
            if len(options) > 0:
                raise ResourceError(f"invalid option '{options[0]}")
                return E_INVALID
            if value:
                if not value in list(resources.data):
                    app.error(f"'{item}' is not a valid resource name")
                    return app.E_NOTFOUND
                data = resources.properties(name=value)
            else:
                data = resources.PROPERTIES
            outputter(data,**outputter_options)
            return app.E_OK

        elif key in ["--index"]:
            if not value:
                app.error("missing resource name")
                return E_MISSING
            for item in value: # TODO only one allowed
                if not item in resources.data:
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
            if not result is None:
                outputter(result,**outputter_options)
            else:
                app.error(f"{resources.request.url}: {resources.request.content.decode('utf-8')}")
                return E_FAILED
            return app.E_OK

        elif key in ["--test"]:
            for pattern in value if value else ['.*']:
                rc = test(pattern)
                if re != app.E_OK:
                    return rc

        else:
            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID



    return app.E_OK

def test(pattern='.*'):
    """Run tests on resources that match the specified pattern

    Arguments:

    * `pattern`: the resource name as a regular expression

    Returns:

    * Exit code: E_OK on success, E_FAILED on failure
    """
    resource = Resource()
    tested = 0
    failed = 0
    checked = 0
    for name in resource.list(pattern):
        print(f"*** Testing resource '{name}' ***",file=sys.stderr)
        print("Properties:",file=sys.stderr)
        for key,value in resource.properties(name=name).items():
            print(f"  {key}: {repr(value)}",file=sys.stderr)
        index = resource.index(name=name)
        if index:
            for item in index:
                try:
                    tested += 1
                    content = resource.headers(name=name,index=item)
                    size = content['content-length']
                    checked += int(size.split()[0])
                    print(f"{name}/{item}... {size} bytes",flush=True,file=sys.stderr)
                except Exception as err:
                    failed += 1
                    print(f"FAILED: {name}... {err}",file=sys.stderr)

    print(f"Tested {tested} resources ({checked/1e6:.1f} MB) with {failed} failures",file=sys.stderr)
    return app.E_OK if failed == 0 else app.E_FAILED

if __name__ == "__main__":

    # local development tests
    # TODO: comment this block entire when done developing
    if not sys.argv[0]:

        test()

        #
        # Test library functions (comprehensive scan of all contents)
        #
        # sys.argv = [__file__,"--test"]
        # sys.argv = [__file__,"--test=buildings"]
        # sys.argv = [__file__,"--test=elevation"]
        # sys.argv = [__file__,"--test=examples"]
        # sys.argv = [__file__,"--test=geodata"]
        # sys.argv = [__file__,"--test=icons"]
        # sys.argv = [__file__,"--test=library"]
        # sys.argv = [__file__,"--test=models"]
        # sys.argv = [__file__,"--test=tariff"]
        # sys.argv = [__file__,"--test=template"]
        # sys.argv = [__file__,"--test=version"]
        # sys.argv = [__file__,"--test=weather"]

        #
        # Test command line options (e.g., one at a time)
        #

        # options = []
        # options.extend(["--debug"])
        # options.extend(["--verbose"])
        # options.extend(["--format=csv"])
        # options.extend(["--format=csv,fmt:.0f"])
        # options.extend(["--format=json,indent:4"])
        # options.extend(["--format=json,indent:4,orient:index"])
        
        # sys.argv = [__file__,*options,"--list"]
        # sys.argv = [__file__,*options,"--list=[a-l]"]

        # sys.argv = [__file__,*options,"--index=buildings"]
        # sys.argv = [__file__,*options,"--index=code"]
        # sys.argv = [__file__,*options,"--index=elevation"]
        # sys.argv = [__file__,*options,"--index=examples"]
        # sys.argv = [__file__,*options,"--index=geodata"]
        # sys.argv = [__file__,*options,"--index=icons"]
        # sys.argv = [__file__,*options,"--index=library"]
        # sys.argv = [__file__,*options,"--index=models"]
        # sys.argv = [__file__,*options,"--index=tariff"]
        # sys.argv = [__file__,*options,"--index=template"]
        # sys.argv = [__file__,*options,"--index=version"]
        # sys.argv = [__file__,*options,"--index=weather"]

        # sys.argv = [__file__,*options,"--properties"]
        # sys.argv = [__file__,*options,"--properties=buildings"]
        # sys.argv = [__file__,*options,"--properties=code"]
        # sys.argv = [__file__,*options,"--properties=elevation"]
        # sys.argv = [__file__,*options,"--properties=examples"]
        # sys.argv = [__file__,*options,"--properties=geodata"]
        # sys.argv = [__file__,*options,"--properties=icons"]
        # sys.argv = [__file__,*options,"--properties=library"]
        # sys.argv = [__file__,*options,"--properties=models"]
        # sys.argv = [__file__,*options,"--properties=tariff"]
        # sys.argv = [__file__,*options,"--properties=template"]
        # sys.argv = [__file__,*options,"--properties=version"]
        # sys.argv = [__file__,*options,"--properties=weather"]

        # sys.argv = [__file__,*options,"--content=buildings,US/ME_Aroostook.csv.gz"]
        # sys.argv = [__file__,*options,"--content=code,COPYRIGHT"]
        # sys.argv = [__file__,*options,"--content=elevation,10m/31N_112W.tif"]
        # sys.argv = [__file__,*options,"--content=examples,geodata/IEEE-123.json"]
        # sys.argv = [__file__,*options,"--content=geodata,census/income_CA.csv"]
        # sys.argv = [__file__,*options,"--content=icons,pole.png"]
        # sys.argv = [__file__,*options,"--content=library,US/CA/SLAC/pole_configuration.glm"]
        # sys.argv = [__file__,*options,"--content=models,gridlabd-4/IEEE/13.glm"]
        # sys.argv = [__file__,*options,"--content=tariff,rates.csv.gz"]
        # sys.argv = [__file__,*options,"--content=template,US/CA/SLAC/electrification/electrification.md"]
        # sys.argv = [__file__,*options,"--content=version,4.3.2"]
        # sys.argv = [__file__,*options,"--content=weather,US/WA-Seattle_Seattletacoma_Intl_A.tmy3"]

        # sys.argv = [__file__,*options,"--index"] # should be an error
        # sys.argv = [__file__,*options,"--index=localhost"] # should be an error
        # sys.argv = [__file__,*options,"--content=localhost"] # should be an error
        # sys.argv = [__file__,*options,"--content=junk"] # should be an error

    app.run(main)
