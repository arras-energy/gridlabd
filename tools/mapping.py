"""Mapping utilities

Syntax: `gridlabd mapping FILENAME [OPTIONS ...]`

Options:

* `--save=FILENAME`: save the image to FILENAME

* `--show[=OPTIONS]`: open the image in a browser using the
  `plotly.scattermap` options

* `-h|--help|help`: output this help to stdout

* `--debug`: enable debug and traceback output on exceptions to stderr

* `--verbose`: enable verbose output to stderr

* `--quiet`: disable error output to stderr

* `--silent`: disable output to stdout

* `--warning`: disable warning output to stderr

Description:

The `mapping` tool generates a map of the network contained in the model
`FILENAME` using `plotly`'s `scattermap` or `scattermapbox` API.  The
configuration file `mapping_config.py` specifies the mapping options
according to the map style selected, e.g., `map` or `mapbox`. The default
mapping configuration is found in the gridlabd shared folder.

Two network modules are currently supported, `powerflow` and `pypower`.
Symbols for various object types and hover popups can be configured in the
mapping configuration file.

Examples:

To generate a map image use the `--save` option, e.g.,

    gridlabd mapping mymodel.json --save=mymodel.png

To open a map in the default browser use the `--show` option, e.g.,

    gridlabd mapping mymodel.json --show

See also:

* [[/Module/Powerflow]]

* [[/Module/Pypower]]

* [Plotly Scattermapbox reference](https://plotly.com/python/reference/scattermapbox/)

* [Plotly Scattermap reference](https://plotly.com/python/reference/scattermap/)

"""
import os
import sys
import io
import json
import math
import pandas as pd
import plotly.express as px
import unitcalc
from typing import TypeVar
import traceback

from framework import *

DEFAULT_MAPPER = "map" # "map" or "mapbox"

#
# Load custom mapping configuration (if any)
#
try:

    import mapping_config as config

except ModuleNotFoundError:

    class config:
        mapper = DEFAULT_MAPPER
        defaults = {
            "lat" : "latitude",
            "lon" : "longitude",
            f"{DEFAULT_MAPPER}_style" : "open-street-map",
            "zoom" : 2.7,
            "center" : {"lat":40,"lon":-96},
        }
        network = {
            "powerflow" : {
                "ref":("bustype","SWING"),
                "nodes":["from","to"],
                },
            "pypower" : {
                "ref":("type","3"),
                "nodes":["fbus","tbus"],
                },
        }
        violation_color = {
            "NONE" : (0,0,0),
            "THERMAL" : (1,0,0),
            "CURRENT" : (0.5,0,0),
            "POWER" : (0,1,0),
            "VOLTAGE" : (0,0,1),
            "CONTROL" : (0,0,0.5),
        }
        node_options = {
            "textposition" : "top right",
            # Slows mapping down alot and doesn't display links
            # "cluster" : {
            #     "enabled" : False,
            #     "maxzoom" : 12,"
        }

def main(argv:list[str]) -> int:
    """Command line processing

    Arguments:

    * `argv`: command line arguments

    Returns:

    * exit code
    """
    argc = len(argv)

    if argc == 1:

        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]))
        return E_SYNTAX

    args = read_stdargs(argv)

    fig = None

    for key,value in args:

        if key in ["-h","--help","help"]:

            print(__doc__,file=sys.stdout)

            return E_OK

        if key in ["--save"]:

            if len(value) == 0:
                error("missing filename")
                return E_MISSING

            options = get_options(value[1:],{"center":"auto","zoom":14})
            fig.save(value[0],**options)

        elif key in ["--show"]:

            options = get_options(value,{"center":"auto","zoom":14})
            fig.show(
                hover_name="name",
                hover_data={
                    "name":False,
                    "latitude":False,
                    "longitude":False,
                    "class":True,
                    'voltage_A':True,
                    'voltage_B':True,
                    'voltage_C':True,
                    },
                **options
            )

        elif fig is None:

            if key.endswith(".glm"):
                file = open_glm(key)
            elif key.endswith(".json"):
                file = open(key,"r")
            else:
                raise MapError("unknown input file format")
            fig = Map(file,
                nodedata={
                    "latitude": float,
                    "longitude": float,
                    "voltage_A": lambda x:complex_unit(x,'d'),
                    "voltage_B": lambda x:complex_unit(x,'d'),
                    "voltage_C": lambda x:complex_unit(x,'d'),
                    "class": str,
                    },
                linkdata={
                    "status": str,
                    "class": str,
                    # "power_in":lambda x:complex_unit(x,'j'),
                    # "power_out":lambda x:complex_unit(x,'j'),
                    # "current_in_A":lambda x:complex_unit(x,'j'),
                    # "current_in_B":lambda x:complex_unit(x,'j'),
                    # "current_in_C":lambda x:complex_unit(x,'j'),
                    }
                )

        else:

            error(f"'{key}={value}'' is invalid")

            return E_SYNTAX

    return E_OK

def get_options(value:str,default:dict=None) -> dict:
    """Extract save/show options from argument value

    Arguments:

    * `value`: the argument text

    * `default`: the default value to use for any options not specified

    Returns:

    * the option values
    """
    options = {} if default is None else default
    if not value:
        value = []
    for key in value:
        x,y = key.split(":",1)
        try:
            if x == "center" and ";" in y:
                options[x] = {["lat","lon"][n]:float(z) for n,z in enumerate(y.split(";"))}
            elif x in ["zoom","width","height"]:
                options[x] = int(y)
            else:
                options[x] = y
        except:
            options[x] = y

    return options

class MapError(Exception):
    """Mapping exception"""
    pass

class Map:
    """Mapping class"""
    defaults = config.defaults
    network = config.network
    violation_color = config.violation_color

    def __init__(self,
            model:[dict,str,TypeVar('io.TextIOWrapper')]=None,
            nodedata:dict={},
            linkdata:dict={},
            **options):
        """Construct a map from a model

        Arguments:

        * `model`: dict, json file handle, json data

        * `nodedata`: data extraction/formatting for node hover

        * `linkdata`: data extraction/formatting for link hover

        * `options`: plotly scattermap options

        See also: 

        * [[/Module/Powerflow]]

        * [[/Module/Pypower]]

        * https://plotly.com/python/reference/scattermapbox/

        * https://plotly.com/python/reference/scattermap/
        """
        self.options = options if options else {}
        self.data = pd.DataFrame({"latitude":[],"longitude":[]})
        for key,value in self.defaults.items():
            if not key in self.options:
                self.options[key] = value
        if model is None:
            self.read({
                "application":"gridlabd",
                "version":version(),
                "modules":{},
                "classes":{},
                "objects":{}
            })
        elif isinstance(model,dict):
            self.read(model,nodedata,linkdata)
        elif isinstance(model,str):
            self.read(json.loads(model),nodedata,linkdata)
        elif isinstance(model,io.TextIOWrapper):
            self.read(json.load(model),nodedata,linkdata)
        else:
            raise ValueError("model is not a valid str or io object")
        self.map = None

    def read(self,data:dict,nodedata:dict={},linkdata:dict={}):
        """Read JSON data

        Arguments:

        * `data`: the gridlabd model data

        * `nodedata`: node data to extract/format

        * `linkdata`: link data to extract/format

        See also:

        * [[/Module/Powerflow]]

        * [[/Module/Pypower]]
        """
        try:
            assert "application" in data, "invalid application data"
            assert data["application"] == "gridlabd", "invalid gridlabd model"
            assert "version" in data, "missing gridlabd version"
            assert "modules" in data, "missing module data"
            assert "classes" in data, "missing class data"
            assert "objects" in data, "missing object data"
        except AssertError as err:
            raise MapError(str(err)) from err
        self.model = data
        self.extract_network(nodedata,linkdata)

    def extract_network(self,nodedata:dict={},linkdata:dict={}) -> list[str]:
        """Extract network data

        Arguments:

        * `nodedata`: nodedata to extract/format

        * `linkdata`: linkdata to extract/format

        Returns:

        * list of swing busses found, if any

        See also:

        * [[/Module/Powerflow]]

        * [[/Module/Pypower]]
        """
        self.links = {}
        self.nodes = {}
        self.swing = set()

        # add data needed for mapping
        for x,y in {self.defaults["lat"]:float,self.defaults["lon"]:float}.items():
            if x not in nodedata:
                nodedata[x] = y
        for x,y in {
                "class":str,
                "phases":str,
                "flow_direction":str,
                "violation_detected":str,
                "power_out":lambda x:complex_unit(x,'real')
                }.items():
            if x not in linkdata:
                linkdata[x] = y

        # extract objects
        for name,data in self.model["objects"].items():

            # handle objects according to modules loaded
            for module in [x for x in self.model["modules"] \
                    if x in self.network]:

                # get from/to tags used by the module
                ftag,ttag = self.network[module]["nodes"]

                # if tags present in data
                if ftag in data and ttag in data:

                    # get from/to nodes
                    n0,n1 = data[ftag],data[ttag]

                    # extract link data
                    self.links[name] = {
                        "nodes": [n0,n1],
                        "data": {key:data[key] for key in linkdata if key in data},
                        }

                    # extract node data
                    for n in [n0,n1]:
                        if not n in self.nodes:
                            self.nodes[n] = {
                                "links":set(),
                                "data":{key:dtype(self.model["objects"][n][key]) \
                                    for key,dtype in nodedata.items() \
                                    if key in self.model["objects"][n]},
                                }
                        self.nodes[n]["links"].add(name)

                # record any swing nodes for future reference
                elif self.network[module]["ref"][0] in data \
                        and data[self.network[module]["ref"][0]] == self.network[module]["ref"][1]:
                    self.swing.add(name)

        # contract mapping dataframe
        self.data = pd.DataFrame(
            data=[x["data"] for x in self.nodes.values()],
            index=self.nodes.keys(),
            columns=nodedata.keys(),
            )
        self.data.index.name = "name"
        self.data.reset_index(inplace=True)

        # return swing node list
        return self.swing

    def render(self,**options) -> TypeVar('plotly.graph_objects.Figure'):
        """Render the map

        Arguments:

        * `options`: plotly scattermap options

        Returns:

        * plotly figure

        See also: 

        * https://plotly.com/python/reference/scattermapbox/

        * https://plotly.com/python/reference/scattermap/
        """
        for key,value in options.items():
            self.options[key] = value
        for key,value in self.options.items():
            if key == 'zoom' and value == 'auto':
                self.options["zoom"] = 10
            elif key == 'center' and value == 'auto':
                lat = self.defaults["lat"]
                lon = self.defaults["lon"]
                lat = (self.data[lat].min()+self.data[lat].max())/2
                lon = (self.data[lon].min()+self.data[lon].max())/2
                self.options["center"] = {"lat" : lat,"lon" : lon,}

        self.map = getattr(px,f"scatter_{config.mapper}")(self.data.dropna(),
            **self.options)
        lat,lon = [self.defaults[x] for x in ["lat","lon"]]
        for key,value in self.links.items():
            n0,n1 = [self.model["objects"][x] for x in value["nodes"]]
            if lat in n0 and lon in n0 and lat in n1 and lon in n1:
                data = value["data"]
                phases = data["phases"]
                width = len(phases)
                color = "#"+"".join([f"{int(255*x):02x}" for x in self.violation_color[data["violation_detected"]]])
                x0,y0,x2,y2 = float(n0[lat]),float(n0[lon]),float(n1[lat]),float(n1[lon])
                x1,y1 = (x0+x2)/2,(y0+y2)/2
                self.map.add_scattermap(
                    lat=[x0,x2],
                    lon=[y0,y2],
                    line={
                        "color": color,
                        "width": width,
                        },
                    mode="lines",
                    hoverinfo="skip",
                    showlegend=False,
                    )
                if hasattr(config,"node_options"):
                    self.map.update_traces(**config.node_options,selector={"type":f"scatter{config.mapper}"})
                power_out = complex_unit(data["power_out"],'real')
                symbols = {
                    "switch" : "square-stroked" if power_out<0.1 else "square",
                    "transformer" : "circle-stroked",
                    "regulator" : "circle-stroked",
                    }
                devtype = data["class"]
                flow = data["flow_direction"]
                if devtype in symbols:
                    symbol = symbols[devtype]
                else:
                    symbol = "triangle"
                    if "R" not in flow:
                        direction = 1
                    elif "F" not in flow:
                        direction = -1
                    else:
                        symbol = "diamond"

                self.map.add_scattermap(
                    lat=[x1],
                    lon=[y1],
                    marker={
                        "symbol" : symbol,
                        "size": width+5,
                        "allowoverlap": True,
                        "color": color,
                        "angle": math.atan2(direction*(y2-y0),direction*(x2-x0))*180/3.1416,
                    },
                    mode="markers",
                    showlegend=False,
                    hovertemplate=f"<extra></extra><b>{key}</b><br><br>" + "<br>".join([f"{x}={y}" for x,y in data.items()]),
                    )
        return self.map

    def show(self,**options):
        """Open the map in a browser window

        Arguments:

        * `options`: plotly render options

        See also: 

        * https://plotly.com/python/reference/scattermapbox/

        * https://plotly.com/python/reference/scattermap/
        """
        if not self.map or options != self.options:
            self.render(**options)
        self.map.show()

    def save(self,name:str=None,**options):
        """Save the map in a file

        Arguments:

        * `options`: plotly render options
        """
        if not self.map or options != self.options:
            self.render(**options)
        self.map.write_image(name)

if __name__ == "__main__":

    try:

        rc = main(sys.argv)
        exit(rc)

    except SystemExit:

        pass

    except KeyboardInterrupt:

        exit(E_INTERRUPT)

    except Exception as exc:

        if DEBUG:
            raise exc

        if not QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[1]
            print(f"EXCEPTION [{os.path.basename(tb.filename)}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(E_EXCEPTION)
