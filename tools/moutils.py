"""Marimo utilities
"""
import os
import io
import json
import math
from collections import namedtuple
import marimo as mo
import subprocess
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import random

def gridlabd(*args, bin=True, **kwargs):
    if not "capture_output" in kwargs:
        kwargs["capture_output"] = True
    try:
        return subprocess.run(
            ["gridlabd.bin" if bin else "gridlabd"] + list(args), **kwargs
        )
    except:
        return None

def _icon(name):
    return mo.icon(f"lucide:{name}")

version = gridlabd("--version")
version = version.stdout.decode('utf-8').strip() if version and version.returncode==0 else ""

def render_sidebar(upload):
    items = {
        f"**{upload.name(0)}**" : {
            "#/map": f"{_icon('locate')} Map",
            "#/objects": f"{_icon('table-properties')} Objects",
            "#/globals": f"{_icon('globe')} Globals",
            # "#/modules": f"{_icon('package')} Modules",
            # "#/classes": f"{_icon('component')} Classes",
        }
    } if len(upload.value) > 0 else {}
    helps = {
        f"{_icon('chevrons-left-right-ellipsis')} GridLAB-D Online": {
            "https://www.arras.energy/": f"{_icon('info')} Arras Energy",
            "https://docs.gridlabd.us/": f"{_icon('circle-help')} Documentation",
            "https://arras.energy/": f"{_icon('github')} Resources",
            "https://github.com/orgs/arras-energy/discussions" : f"{_icon('users')} Community",
            "https://github.com/arras-energy/gridlabd/issues" : f"{_icon('bug-off')} Issues"
        },    
    }
    return mo.vstack([
        mo.md(f"# GridLAB-D\n{version}"),
        mo.nav_menu(items,orientation="vertical"),
        mo.nav_menu(helps,orientation="vertical"),
        ])

def model(source,folder="/tmp"):
    _pathname = os.path.join(folder,source.name(0))
    _dir,_file = os.path.dirname(_pathname),os.path.basename(_pathname)
    _name,_ext = os.path.splitext(_file)
    mo.stop(not _ext in [".glm",".json"],f"ERROR: '{_ext}' is not a valid GridLAB-D file type")
    _result = None
    if _ext == ".glm":
        open(_pathname,"w").write(source.contents(0).decode('utf-8'))
        _jsonname = os.path.join(_dir,_name+".json")
        with mo.status.spinner("Converting to JSON...") as spinner:
            _converter = gridlabd("-C",_pathname,"-o",_jsonname)
            mo.stop(_converter.returncode!=0,_converter.stderr.decode("utf-8"))
        _result = _converter.stdout.decode("utf-8")
    else:
        _jsonname = _pathname
    _io = open(_jsonname,"r")
    _model = json.load(_io)
    mo.stop("application" not in _model,"model does not contain GridLAB-D application data")
    return namedtuple("model",_model.keys())(*_model.values()),_result

def _table(model,module=None):
    def _name(x):
        return (x.split('::',1)[1] if '::' in x else x).replace('_',' ').title()
    def _text(x):
        def _modify(x,y):
            model.globals[x]['value'] = y
        return mo.ui.text(value=model.globals[x]['value'],
                          on_change=lambda y:_modify,
                          full_width=True
                         )
    def _item(x):
        return f"<tr><th width=250>{_name(x)}</th><td width=450>{_text(x)}</td></tr>"

    _items = [
        _item(x)
        for x in sorted(model.globals)
        if (module is None and not "::" in x)
        or (isinstance(module, str) and x.startswith(module + "::"))
    ]
    return mo.md("\n".join(["<table>"] + _items + ["</table>"]))

def render_globals(model,module=None):
    result = {"System": _table(model)}
    if module is None:
        for module in model.modules:
            result[module.replace("_", " ").title()] = _table(model,module)
    return mo.vstack([mo.md("# Globals"),mo.ui.tabs(result)])

def render_modules(model):
    return mo.md("# Modules")

def render_status(model):
    return mo.md(f"# {get_modelname()}\n{len(model.objects)} objects found.")

def render_classes(model):
    return mo.md("# Classes")

# Render objects
def _objects(model,cls):
    # return mo.vstack([mo.md(x) for x,y in model.objects.items() if y["class"] == cls and "latitude" not in y and "longitude" not in y])
    return mo.vstack([mo.md(x) for x,y in model.objects.items() if y["class"] == cls])

def render_objects(model):
    def _name(x):
        return x.replace('_',' ').title()

    _classes = sorted(list(set([x["class"] for x in model.objects.values()])))
    _stacks = {f"**{_name(x)}**":_objects(model,x) for x in _classes}
    return mo.vstack([mo.md("# Objects"),
                  mo.accordion(_stacks,multiple=True)
                  ])

def render_map(model,**kwargs):
    _data = pd.DataFrame({"latitude":[],"longitude":[]})
    _params = {"lat":"latitude","lon":"longitude","map_style":"open-street-map"}
    if not "zoom" in kwargs:
        kwargs["zoom"] = 2.75
    if not "center" in kwargs:
        kwargs["center"] = {"lat":40,"lon":-96}
    map = px.scatter_map(_data,**_params,**kwargs)
    return map

def float_unit(x):
    return float(x.split(" ",1)[0])

def complex_unit(x,form=None):
    if form is str:
        return x
    z,u = x.split(" ",1)
    z = complex(z)
    if form is None:
        return z
    x,y = z.real,z.imag
    if form in ['i','j']:
        return f"{x:.2f}{y:+.2f}{form}"        
    if form == 'rect':
        return x,y
    if form == 'd':
        return f"{abs(z):.2f}{math.atan2(x,y)*180/3.1416:+.1f}d"
    if form == 'r':
        return f"{abs(z):.2f}{math.atan2(x,y):+.3f}r"
    if form == 'real':
        return z.real
    if form == 'imag':
        return z.imag
    if form == 'mag':
        return abs(z)
    if form == 'arg':
        return math.atan2(x,y)
    if form == 'ang':
        return math.atan2(x,y)*180/3.1416
    return getattr(x,form)

try:
    import mapinfo as config
except ModuleNotFoundError:
    class config:
        defaults = {
            "lat" : "latitude",
            "lon" : "longitude",
            "map_style" : "open-street-map",
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

class Map:

    defaults = config.defaults
    network = config.network
    violation_color = config.violation_color

    def __init__(self,model=None,nodedata={},linkdata={},**options):
        """Initialize"""
        self.options = options if options else {}
        self.data = pd.DataFrame({"latitude":[],"longitude":[]})
        for key,value in self.defaults.items():
            if not key in self.options:
                self.options[key] = value
        if model is None:
            self.read({
                "application":"gridlabd",
                "version":version,
                "modules":{},
                "classes":{},
                "objects":{}
            })
        elif isinstance(model,str):
            self.read(json.loads(model),nodedata,linkdata)
        elif isinstance(model,io.TextIOWrapper):
            self.read(json.load(model),nodedata,linkdata)
        else:
            raise ValueError("model is not a valid str or io object")
        self.map = None

    def read(self,data,nodedata={},linkdata={}):
        """Read JSON data"""
        assert "application" in data, "invalid application data"
        assert data["application"] == "gridlabd", "invalid gridlabd model"
        assert "version" in data, "missing gridlabd version"
        assert "modules" in data, "missing module data"
        assert "classes" in data, "missing class data"
        assert "objects" in data, "missing object data"
        self.model = data
        self.extract_network(nodedata,linkdata)

    def extract_network(self,nodedata={},linkdata={}):
        """Extract network data"""
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

    def render(self,**options):
        for key,value in options.items():
            self.options[key] = value
        for key,value in self.options.items():
            if key == 'zoom' and value == 'auto':
                self.options["zoom"] = 10
            if key == 'center' and value == 'auto':
                lat = self.defaults["lat"]
                lon = self.defaults["lon"]
                lat = (self.data[lat].min()+self.data[lat].max())/2
                lon = (self.data[lon].min()+self.data[lon].max())/2
                self.options["center"] = {"lat" : lat,"lon" : lon,}
        self.map = px.scatter_map(self.data.dropna(),
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
        if not self.map or options != self.options:
            self.render(**options)
        self.map.show()

    def save(self,name=None,**options):
        if not self.map or options != self.options:
            self.render(**options)
        self.map.write_image(name)

if __name__ == "__main__":

    try:
        import kaleido
    except:
        os.system("pip install --upgrade kaleido >/dev/null 2>&1")
        import kaleido

    map = Map(open("autotest/test_moutils.json","r"),
        nodedata={
            "latitude":float,"longitude":float,
            "voltage_A":lambda x:complex_unit(x,'d'),
            "voltage_B":lambda x:complex_unit(x,'d'),
            "voltage_C":lambda x:complex_unit(x,'d'),
            "class":str,
            },
        linkdata={
            # "power_in":lambda x:complex_unit(x,'j'),
            # "power_out":lambda x:complex_unit(x,'j'),
            # "current_in_A":lambda x:complex_unit(x,'j'),
            # "current_in_B":lambda x:complex_unit(x,'j'),
            # "current_in_C":lambda x:complex_unit(x,'j'),
            }
        )
    map.save("autotest/test_moutils.png",
        center='auto',zoom=15,
        )
    map.show(
        # text='name',
        hover_name="name",
        hover_data={
            "name":False,"latitude":False,"longitude":False,
            "class":True,
            'voltage_A':True,'voltage_B':True,'voltage_C':True,
            }
)
