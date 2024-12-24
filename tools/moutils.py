"""Marimo utilities
"""
import os
import io
import json
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

class Map:

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

    def __init__(self,model=None,nodedata=[],linkdata=[],**options):
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

    def read(self,data,nodedata=[],linkdata=[]):
        """Read JSON data"""
        assert "application" in data, "invalid application data"
        assert data["application"] == "gridlabd", "invalid gridlabd model"
        assert "version" in data, "missing gridlabd version"
        assert "modules" in data, "missing module data"
        assert "classes" in data, "missing class data"
        assert "objects" in data, "missing object data"
        self.model = data
        self.extract_network(nodedata,linkdata)

    def extract_network(self,nodedata=[],linkdata=[]):
        """Extract network data"""
        self.links = {}
        self.nodes = {}
        self.swing = set()
        for name,data in self.model["objects"].items():
            for module in self.model["modules"]:
                ftag,ttag = self.network[module]["nodes"]
                if ftag in data and ttag in data:
                    n0,n1 = data[ftag],data[ttag]
                    self.links[name] = {
                        "nodes": [n0,n1],
                        "data": {key:data[key] for key in linkdata if key in data},
                        }
                    for n in [n0,n1]:
                        if not n in self.nodes:
                            self.nodes[n] = {
                                "links":set(),
                                "data":{key:self.model["objects"][n][key] for key in nodedata if key in self.model["objects"][n]},
                                }
                        self.nodes[n]["links"].add(name)
                elif self.network[module]["ref"][0] in data \
                        and data[self.network[module]["ref"][0]] == self.network[module]["ref"][1]:
                    self.swing.add(name)
        # print(self.links,self.nodes,self.swing)
        return


    def render(self):
        self.map = px.scatter_map(self.data,**self.options)
        return self.map

    def show(self):
        if not self.map:
            self.render()
        self.map.show()

    def save(self,name=None):
        if not self.map:
            self.render()
        self.map.write_image(name)

if __name__ == "__main__":

    try:
        import kaleido
    except:
        os.system("pip install --upgrade kaleido >/dev/null 2>&1")
        import kaleido

    map = Map(open("autotest/test_moutils.json","r"),
        nodedata=["latitude","longitude","voltage_A","voltage_B","voltage_C"],
        linkdata=["power_in","power_out"]
        )
    map.save("autotest/test_moutils.png")

