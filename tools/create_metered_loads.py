# Syntax: create_metered_loads [-i|--input=INPUTFILE] [-o|--output=GLMFILE] [OPTIONS ...]
"""Syntax: create_metered_loads [-i|--input=INPUTFILE] [-o|--output=GLMFILE] [OPTIONS ...]

Options
-------
    -P|--parents=NAME:VALUE,... specify parent property pattern to match (required)
    -C|--childs=NAME:VALUE,...  specify child property list to assign (required)
    -N|--names=STRING           specify object naming convention (default is '{class}_{name}')
    -M|--modules=NAME,...       specify module names to use (defaults to those found)
    -L|--link=NAME:VALUE....    specify link types (required)

Description
-----------

The `create_metered_loads` tool adds loads with meter objects to all objects that match the
parent object pattern specified.

Parent patterns and child properties as specified as a comma-separate list of
`NAME:VALUE` strings, e.g., `class:node` or `nominal_voltage:2.4kV`. Parent
patterns use `regex` pattern matching. Child properties may include `{NAME}` 
format strings where `NAME` is a property of the parent object. This
allows copying of values from the parent object. This formatting also can be
applied to the naming string, e.g., `-N='{name}_L' to append '_L' to the
parent object name.

Example
-------

The following creates a GLM file containing a `triplex_load` objects attached
to `triplex_node` objects with names starting as `N_` in the file `my-network.json`:

~~~
$ gridlabd create_metered_loads -i=my-network.json -o=loads.glm -P='class:triplex_node,name:^N_' -C='class:triplex_load,nominal_voltage:{nominal_voltage},phases:{phases},constant_power_B:1.2+0.1jkVA'
~~~
"""



import sys, os
import json
import re
import datetime
import subprocess
import random

EXENAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]

DEBUG = False
WARNING = True
QUIET = False
VERBOSE = False

E_OK = 0
E_INVALID = 1
E_FAILED = 2
E_SYNTAX = 8
E_EXCEPTION = 9
EXITCODE = E_OK

class GldException(Exception):
    pass

def error(msg,code=None):
    if type(code) is int:
        global EXITCODE
        EXITCODE = code
    if DEBUG:
        raise GldException(msg)
    print("ERROR [create_metered_loads]:",msg,file=sys.stderr)
    exit(code)


def load():

    if not INPUTFILE.endswith(".json"):
        tmpfile = "."
        while os.path.exists(tmpfile):
            tmpfile = f"tmp{hex(random.randint(1e30,1e31))[2:]}.json"
        try:
            result = subprocess.run(["gridlabd","-C",INPUTFILE,"-o",tmpfile])
            assert(result.returncode==0)
            with open(tmpfile,"r") as fh:
                model = json.load(fh)
        except:
            raise
        finally:
            os.remove(tmpfile)
            pass
    else:
        with open(INPUTFILE,"r") as fh:
            model = json.load(fh)
    return model

def save(fh):
    print(f"// generated by '{' '.join(sys.argv)}' at {datetime.datetime.now()}",file=fh)
    for name in MODULES:
        print(f"module {name};",file=fh)
    classname = CHILDS["class"]
    link_class = LINK["class"]
    if classname == "load" : 
        meter_class = "meter"
    elif classname == "triplex_load" : 
        meter_class = "triplex_meter"
    for obj,data in OBJECTS.items():
        if "meter" in obj : 
            print(f"object {meter_class} {{",file=fh)
        elif "link" in obj :
            print(f"object {link_class} {{",file=fh)
        else : 
            print(f"object {classname} {{",file=fh)
        for prop,value in data.items():
            print(f"    {prop} \"{value}\";",file=fh)
        print("}",file=fh)

def main():

    PATTERN = {}
    for name,pattern in PARENTS.items():
        PATTERN[name] = re.compile(pattern)

    if "class" not in CHILDS:
        error("you must include a class name in the child properties",E_INVALID)
    classname = CHILDS["class"]
    model = load()
    assert(model['application']=='gridlabd')
    global MODULES
    if not MODULES:
        MODULES = list(model['modules'])

    for obj,data in model['objects'].items():
        data['name'] = obj
        ok = True
        for name,pattern in PATTERN.items():
            if not pattern.match(data[name]):
                ok = False
                break
        if ok:
            name = f"{classname}_{obj}" if NAMING is None else NAMING.format(**data)
            name_meter = f"meter_{obj}" 
            name_link = f"link_{obj}"
            OBJECTS[name_meter] = dict(name=name_meter)
            OBJECTS[name] = dict(parent=name_meter,name=name)
            OBJECTS[name_link] = dict(name=name_link, to=name_meter)
            OBJECTS[name_link]["from"] = obj

            for prop,value in CHILDS.items():
                if not prop in ["class"]:
                    OBJECTS[name][prop] = value.format(**data)
                if prop in ["phases"]:
                    OBJECTS[name_meter][prop] = value.format(**data)
                    OBJECTS[name_link][prop] = value.format(**data)
                if prop in ["nominal_voltage"]:
                    OBJECTS[name_meter][prop] = value.format(**data)
            for prop,value in LINK.items():
                if not prop in ["class"]:
                    OBJECTS[name_link][prop] = value.format(**data)


    if OUTPUTFILE.endswith(".glm"):
        with open(OUTPUTFILE,"w") as fh:
            save(fh)
    else:
        error("invalid output file format")

    return E_OK

INPUTFILE = "/dev/stdin"
OUTPUTFILE = "/dev/stdout"
PARENTS = None
CHILDS = None
NAMING = None
OBJECTS = {}
MODULES = []

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print(__doc__.split('\n')[0],file=sys.stderr)
        exit(E_SYNTAX)

    for arg in sys.argv[1:]:
        spec = arg.split("=")
        if len(spec) == 1:
            tag = arg
            value = None
        else:
            tag = spec[0]
            value = '='.join(spec[1:])

        if tag in ["-h","--help","help"]:
            print(__doc__)
            exit(E_OK)
        if tag in ["-i","--input"]:
            INPUTFILE = value if value else "/dev/stdin"
        elif tag in ["-o","--output"]:
            OUTPUTFILE = value if value else "/dev/stdout"
        elif tag in ["-P","--parent"]:
            PARENTS = dict([x.split(":") for x in value.split(",")])
        elif tag in ["-C","--childs"]:
            CHILDS = dict([x.split(":") for x in value.split(",")])
        elif tag in ["-L","--link"]:
            LINK = dict([x.split(":") for x in value.split(",")])
        elif tag in ["-N","--names"]:
            NAMING = value
        elif tag in ["-M","--modules"]:
            MODULES = value.split(",")
        else:
            error(f"option '{arg}' is invalid",E_INVALID)

    if PARENTS is None:
        error("you must specify the parent patterns to match")
    if CHILDS is None:
        error("you must specify the child properties to define")

    EXITCODE = main()
    exit(EXITCODE)