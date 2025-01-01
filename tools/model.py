"""Model edit tool

Syntax: `gridlabd model FILENAME [COMMANDS ...] [OPTIONS ...]`

Options:

* `-s|--save=FILENAME`: save output to FILENAME

Commands:

* `delete=NAME`: delete object NAME from model

Description:

* 
"""

import sys
import os
import json
import re
import traceback
import framework as app

def main(argv:list[str]) -> int:

    if len(argv) == 1:

        print("\n".join([x for x in __doc__.replace("`","").split("\n") if x.startswith("Syntax: ")]))
        return app.E_SYNTAX

    options = app.read_stdargs(argv)

    model = None
    output = None

    for key,value in options:

        app.verbose("key = ",key)
        app.verbose("value = ",value)

        # help
        if key in ["-h","--help","help"]:

            print(__doc__.replace("`",""),file=sys.stdout)

        # output
        elif key in ["-s","--save"]:

            output = value
            if len(output) == 1:
                output.append("w")

        # commands
        elif key in [x for x in dir(GlmEditor) if not x.startswith("_")]:

            kwargs = {x:y for x,y in [z.split(":",1) for z in value if ":" in z]}
            args = [x for x in value if not ":" in x]
            app.verbose("args =",args)
            app.verbose("kwargs =",kwargs)
            if "json" in args:
                form = json.dumps
                args.remove("json")
            else:
                form = None
            call = getattr(model,key)
            app.verbose(call.__name__,args,kwargs)
            result = call(*args,**kwargs)
            app.verbose("->",result)
            if form is None:
                if isinstance(result,list):
                    form = lambda y:"\n".join([str(x) for x in y])
                elif isinstance(result,dict):
                    form = lambda z:"\n".join([f"{x}:{str(y)}" for x,y in z.items()])
                else:
                    raise ValueError("result is not a list or dict")
            if result:
                app.output(form(result),file=sys.stderr)

        # file
        elif model is None:

            if key.endswith(".glm"):

                file,result = app.open_glm(key,passthru=True)

            elif key.endswith(".json"):

                file = open(key)

            else:

                raise RuntimeError("invalid model file type")

            model = GlmEditor(json.load(file))

        # invalid
        else:
            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    if output:
        with open(*output) as fh:
            json.dump(model.data,fh,indent=4)

    return app.E_OK

class GlmEditor:

    def __init__(self,data:dict):
        assert "application" in data, "data does not valid application data"
        assert data["application"] == "gridlabd", "data is not a valid gridlabd model"
        self.data = data

    def list(self,*args,**kwargs):
        """Generate a list of objects

        Arguments:

        * `args`: object name filter patterns (and'ed, default is ".*")

        * `kwargs`: property criteria patterns (and'ed, default is ".*")

        Returns:

        `list`: object names matching criteria
        """
        objects = self.data["objects"]
        if not args:
            result = list(objects.items())
        else:
            for pattern in args:
                result = [x for x,y in objects.items() if re.match(pattern,x)]
        for key,pattern in kwargs.items():
            result = [x for x in result if re.match(pattern,objects[x][key])]
        return result

    def get(self,*args,**kwargs):
        """Get object properties

        Arguments:

        * `args`: object name followed by desired properties pattern (default is ".*")

        * `kwargs`: Ignored
        
        Returns:

        `dict`: object properties
        """
        result = {}
        for name,data in [(x,y) for x,y in self.data["objects"].items() if re.match(args[0],x)]:
            for pattern in args[1:]:
                for key,value in data.items():
                    if re.match(pattern,key):
                        result[f"{name}.{key}"] = value
        return result

    def delete(self,*args,**kwargs):

        objects = self.data["objects"]
        result = []
        if kwargs:
            for name in list(objects):
                for key,pattern in kwargs.items():
                    if name in result:
                        break
                    for x,y in objects[name].items():
                        if re.match(key,x) and re.match(pattern,y):
                            result.append(name)
                            break
            for name in list(result):
                keep = False
                for pattern in args:
                    if re.match(pattern,name):
                        keep = True
                        break
                if not keep:
                    result.remove(name)
        elif args:
            for name in list(objects):
                for pattern in args:
                    if re.match(pattern,name):
                        result.append(name)
                        break
        return result

    def modify(self,*args,**kwargs):

        result = []
        raise NotImplementedError("modify is TODO")
        return result

    def add(self,*args,**kwargs):

        assert "class" in kwargs, "no object class specified"
        oclass = kwargs["class"]
        result = {}
        values = {x:y["default"] for x,y in self.data["classes"][oclass].items() if isinstance(y,dict) and "default" in y}
        for key,value in kwargs.items():
            assert key == "class" or key in values, f"property '{key}' is not valid for class '{oclass}'"
            values[key] = value
        for name in args:
            self.data["objects"][name] = result[name] = values
        return result

if __name__ == "__main__":

    sys.argv = [__file__,
        "autotest/ieee13.glm",
        # "list=Node6[1-4],id:3[23]",
        # "get=Node6,GFA.*",
        # "get=Node633,class,id",
        # "delete=Node633",
        # "delete=(from|to):Node633",
        # "delete=XFMR,(from|to):Node633",
        # "add=Node14,class:node,bustype:SWING",
        "modify=Node14,class:substation",
        "--save=ieee13_out.json",
        # "--verbose",
        # "--debug"
        ]

    try:

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
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[2]
            print(f"EXCEPTION [{app.EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(app.E_EXCEPTION)
