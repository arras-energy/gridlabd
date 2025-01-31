"""Model editor tool

Syntax: `gridlabd edit FILENAME [COMMANDS ...] [OPTIONS ...]`

Options:

* `-s|--save=FILENAME`: save output to `FILENAME`

Commands:

* `add=NAME,PROPERTY:VALUE[,...]`: add an object

* `delete=PATTERN[,PROPERTY:VALUE]`: delete objects

* `get=PATTERN[,PROPERTY:VALUE`: get object data

* `globals=[PATTERN|NAME][,PROPERTY:VALUE]`: get/set globals

* `copy=PATTERN[,PROPERTY:VALUE]`: copy objects 

* `list=PATTERN[,PROPERTY:VALUE]`: list objects

* `modify=PATTERN,PROPERTY:VALUE[,...]`: modify object data

* `move=PATTERN[,PROPERTY:VALUE]`: move objects 

Description:

The model editor utility allows command-line and python-based editing of models.

`PATTERN` is a regular expression used to match objects or global variable
names. `PROPERTY` and `VALUE` can be regular expressions or a property name
and value tuple for get or set operations, respectively. When comma-separated
patterns are allowed, they are interpreted as `and` operations. Note that the
`add` command does not use regular expressions for `NAME`, which are
interpreted literally.

Commands that modify or delete objects or data will output the old value
(s). Output is always generated to `stdout` as a CSV table with property
names in the header row.

The save `FILENAME` format is limited to JSON.

Caveat:

The model editor does not check whether the action will result in a faulty
model, e.g., deleting a node that is referened by a link, adding a property that
is not valid for the class, or changing an object property to something invalid.

Examples:

    gridlabd edit ieee13.glm list='Node6[1-4],id:3[23]'
    gridlabd edit ieee13.glm get='Node6,GFA.*'
    gridlabd edit ieee13.glm get='Node633,class,id'
    gridlabd edit ieee13.glm delete=Node633 --save=ieee13.json
    gridlabd edit ieee13.glm delete=(from|to):Node633 --save=ieee13_out.json
    gridlabd edit ieee13.glm delete=XFMR,(from|to):Node633 --save=ieee13_out.json
    gridlabd edit ieee13.glm add=Node14,class:node,bustype:SWING --save=ieee13_out.json
    gridlabd edit ieee13.glm modify=Node633,class:substation --save=ieee13_out.json
    
"""

import sys
import os
import json
import re
import traceback
from gridlabd import framework as app
import pandas as pd

def to_csv(data,end="\n",sep=",",quote='"',na="",index="name"):
    if isinstance(data,list):
        return end.join([str(x) for x in data if type(x) in [str,float,int,bool,type(None)]])
    elif isinstance(data,dict):
        fields = set()
        for n,values in enumerate(data.values()):
            if isinstance(values,dict):
                fields |= set(list(values.keys()))
            else:
                print(data,file=sys.stderr)
                raise ValueError(f"row {n} data is not a dict")
        fields = list(fields)
        result = [[index]+fields]
        for name,values in data.items():
            row = dict(zip([na]*len(fields),list(fields)))
            for key,value in values.items():
                row[key] = f'{quote}{value}{quote}' if sep in value else str(value)
            result.append([name]+[row[x] if x in row else na for x in fields])
        return end.join([sep.join(row) for row in result])
    elif type(x) in [str,float,int,bool,type(None)]:
        return str(data)

def main(argv:list[str]) -> int:

    options = app.read_stdargs(argv)

    model = None
    output = None
    form = to_csv

    for key,value in options:

        # help
        if key in ["-h","--help","help"]:

            print(__doc__.replace("`",""),file=sys.stdout)

        # output
        elif key in ["-s","--save"]:

            output = value
            if len(output) == 1:
                output.append("w")

        # format
        elif key in ["--json"]:
            form = json.dumps

        # commands
        elif key in [x for x in dir(Editor) if not x.startswith("_")]:

            kwargs = {x:y for x,y in [z.split(":",1) for z in value if ":" in z]}
            args = [x for x in value if not ":" in x]
            call = getattr(model,key)
            app.verbose(f"{call.__name__}({','.join([repr(x) for x in args])}{',' if args and kwargs else ''}{','.join([x+'='+repr(y) for x,y in kwargs.items()])})")
            result = call(*args,**kwargs)
            app.verbose(f"{' '*len(call.__name__)} ->",result)
            app.output(form(result),file=sys.stderr)

        # file
        elif model is None:

            if key.endswith(".glm"):

                file,result = app.open_glm(key,passthru=True)

            elif key.endswith(".json"):

                file = open(key)

            else:

                raise RuntimeError("invalid model file type")

            model = Editor(json.load(file))
            file.close()

        # invalid
        else:
            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    if output:
        with open(*output) as fh:
            if output[0].endswith(".json"):
                json.dump(model.data,fh,indent=4)
            else:
                raise RuntimeError("unsupported output file format")

    return app.E_OK

class Editor:
    """GLM Model Editor
    """
    def __init__(self,data:dict):
        assert "application" in data, "data does not have valid application data"
        assert data["application"] == "gridlabd", "data is not a valid gridlabd model"
        self.data = data

    def list(self,*args,**kwargs):
        """Generate a list of objects

        Arguments:

        * `args`: object name patterns (and'ed, default is ".*")

        * `kwargs`: property criteria patterns (and'ed, default is ".*")

        Returns:

        `list`: object names matching criteria
        """
        objects = self.data["objects"]
        if args:
            for pattern in args:
                result = [x for x,y in objects.items() if re.match(pattern,x)]
        elif kwargs:
            if args:
                result = []
                for pattern in args:
                    result.append([x for x in list(objects) if re.match(pattern,x)])
            else:
                result = list(objects)
            for key,pattern in kwargs.items():
                result = [x for x in result if re.match(pattern,objects[x][key])]
        else:
            result = list(objects)
        return result

    def get(self,*args,**kwargs):
        """Get object properties

        Arguments:

        * `args`: object name pattern followed by desired properties patterns (if any)

        * `kwargs`: key and value patterns to match properties
        
        Returns:

        `dict`: object properties
        """
        result = {}
        for name,data in [(x,y) for x,y in self.data["objects"].items() if re.match(args[0],x)]:
            result[name] = {}
            for key,value in data.items():
                for pattern in args[1:]:
                    if re.match(pattern,key):
                        result[name][key] = value
                for pattern1,pattern2 in kwargs.items():
                    if re.match(pattern1,key) and re.match(pattern2,value):
                        result[name][key] = value

        return result

    def delete(self,*args,**kwargs):
        """Delete objects

        Arguments:

        * `args`: object name pattern followed by desired properties patterns (if any)

        * `kwargs`: key and value patterns to match properties
        
        Returns:

        `dict`: deleted object properties
        """        
        objects = self.data["objects"]
        result = {}
        if kwargs:
            for name in objects:
                for key,pattern in kwargs.items():
                    if name in list(result):
                        break
                    for x,y in objects[name].items():
                        if re.match(key,x) and re.match(pattern,y):
                            result[name] = objects[name]
                            break
            if args:
                for name in list(result):
                    keep = False
                    for pattern in args:
                        if re.match(pattern,name):
                            keep = True
                            break
                    if not keep:
                        del result[name]
        elif args:
            for name in objects:
                for pattern in args:
                    if re.match(pattern,name):
                        result[name] = objects[name]
                        break
        for name in result:
            del self.data["objects"][name]
        return result

    def modify(self,*args,**kwargs):
        """Modify object properties

        Arguments:

        * `args`: object name pattern followed by desired properties patterns (if any)

        * `kwargs`: key and value patterns to match properties
        
        Returns:

        `dict`: object properties prior to modification
        """
        objects = self.data["objects"]
        result = {}
        for pattern in args:
            for name,data in self.data["objects"].items():
                if re.match(pattern,name):
                    result[name] = {}
                    for key,value in kwargs.items():
                        result[name][key] = data[key]
                        self.data["objects"][name][key] = value
        return result

    def add(self,*args,**kwargs):
        """Add objects

        Arguments:

        * `args`: object name pattern followed by desired properties patterns (if any)

        * `kwargs`: key and value patterns to match properties
        
        Returns:

        `dict`: object properties added
        """        
        assert "class" in kwargs, "no object class specified"
        oclass = kwargs["class"]
        result = {}
        values = {x:y["default"] for x,y in self.data["classes"][oclass].items() if isinstance(y,dict) and "default" in y}
        for key,value in kwargs.items():
            assert key == "class" or key in values, f"property '{key}' is not valid for class '{oclass}'"
            values[key] = value
        for name in args:
            result[name] = {}
            self.data["objects"][name] = values
            for key,value in values.items():
                result[name][key] = value
        return result

    def globals(self,*args,**kwargs):
        """Read/write globals

        Arguments:

        * `args`: globals name pattern followed by desired properties patterns (if any)

        * `kwargs`: key and value patterns to get/set globals
        
        Returns:

        `dict`: global properties added
        """        
        result = {}
        for name in args:
            result[name] = self.data["globals"][name]
        for name,value in kwargs.items():
            result[name] = self.data["globals"][name]
            self.data["globals"][name]["value"] = value
        return result

if __name__ == "__main__":

    try:

        if len(sys.argv) == 1:

            print("\n".join([x for x in __doc__.replace("`","").split("\n") if x.startswith("Syntax: ")]))
            exit(app.E_SYNTAX)

        rc = main(sys.argv)
        exit(rc)

    except SystemExit:

        pass

    except KeyboardInterrupt:

        exit(app.E_INTERRUPT)

    except Exception as exc:

        if app.DEBUG:
            raise exc

        if not app.QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[-1]
            print(f"EXCEPTION [{app.EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(app.E_EXCEPTION)
