"""Powerline data tool

Syntax: `gridlabd powerline COUNTRY [STATE [COUNTY]] [OPTIONS ...]

Options:

* `--consolidate={state,county}`: substation consolidate level

* `-o|--output=FILENAME`: output network model to FILENAME

Description:

The `powerline` tool reads the HIFLD transmission line data repository and
generates a network model for the specified region.  The output FILENAME may
a `.glm` or `.json` file.  

If substation consolidation is included, then all the substations at the
specified level are consolidated into a single node with all substation loads
and generation connected at that node.

Example:

See also:

* [[/Tools/Powerplant]]
* [[/Tools/Substation]]
* [HIFLD transmission line data repository](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::transmission-lines/about)
"""
import os
import sys
import io
import requests
import geojson as gj
import pandas as pd
import gridlabd.resource as gr
import gridlabd.framework as app
import gridlabd.substation as substation
import random
import gzip

CONVERTERS = {
    "TYPE" : lambda x: x.replace("; ","|") if x not in ["","NOT AVAILABLE"] else None,
    "STATUS": lambda x: x.replace(" ","_") if x not in ["","NOT AVAILABLE"] else None,
    "OWNER": lambda x: x.title() if x not in ["","NOT AVAILABLE"] else None,
    "VOLTAGE": lambda x: round(float(x),1) if "0" <= x[0] <= "9" else None,
    "SUB_1": lambda x: x.replace(" ","_").replace(".","_") if x not in ["","NOT AVAILABLE"] else None,
    "SUB_2": lambda x: x.replace(" ","_").replace(".","_") if x not in ["","NOT AVAILABLE"] else None,
    "SHAPE_Length": float,
    "from": str,
    "to": str,
}

class PowerlineException(Exception):
    """Powerline class exception handler"""

class Powerline:
    """Powerline class implementation"""
    resource = gr.Resource()

    def __init__(self,*args,consolidate:str=None,**kwargs):
        """Create network class object

        Arguments:

        * `args`: substation class arguments (e.g., `country`, `state`, `county`)

        * `consolidate`: consolidation level desired (e.g., `state`, `county`)

        * `kwargs`: substation class arguments (e.g., filters)
        """
        self._args = args
        self._kwargs = kwargs

        self.bus = substation.Substation(*args,**kwargs).to_dict()

        cachedir = os.path.join(os.environ['GLD_ETC'],".cache","powerline")
        os.makedirs(cachedir,exist_ok=True)
        cachename = os.path.join(cachedir,"powerlines.csv.gz")

        if not os.path.exists(cachename):

            file = self.resource.cache(name="infrastructure",index="powerlines.geojson.gz")
            data = gj.loads(gzip.decompress(open(file,"rb").read()))

            header = []
            rows = []
            n = 0
            for feature in data["features"]:
                properties = feature["properties"]
                if not header:
                    header = [x for x in properties.keys() if x not in ["OBJECTID","geometry","GlobalID"]] + ["from","to"]
                rows.append([properties[x] if x in properties else "" for x in header])
                if "geometry" in properties:
                    geometry = properties["geometry"]
                    # TODO: power line path
                n += 1
            data = pd.DataFrame(rows,columns=header,dtype=str)
            data.set_index("ID").sort_index().to_csv(cachename,header=True,index=True)

        data = pd.read_csv(cachename,index_col="ID",converters=CONVERTERS)
        data.drop([x for x in data.columns if x not in CONVERTERS],inplace=True,axis=1)
        data.columns = [x.lower() for x in data.columns]
        data.index.name = "name"

        self.branch = {x:y for x,y in data.to_dict('index').items() if y['sub_1'] in self.bus and y['sub_2'] in self.bus}
        self.link = {x:y for x,y in data.to_dict('index').items() if ( y['sub_1'] in self.bus or y['sub_2'] in self.bus ) and x not in self.branch}

    def __repr__(self):
        arglist = [repr(x) for x in self._args] + [f"{x}={repr(y)}" for x,y in self._kwargs.items()]
        return f"gridlabd.powerline.Powerline({','.join(arglist)})"

    def write_glm(self,outfile:str):
        """Write GLM

        Arguments:

        * `outfile`: output file name
        """
        with open(outfile,"w") as fh:
            print("module pypower;",file=fh)

            # write node objects
            for node,data in self.bus.items():
                properties = "\n".join([f"    {x.lower()} {data[x]};" for x in ["LATITUDE","LONGITUDE","MIN_VOLT","MAX_VOLT","LINES","COUNTY","CITY","STATE","ZIP","STATUS","COUNTYFIPS","COUNTRY"] if x in data])
                print(f"""object bus
{{
    name "N_{node}";
{properties}
}}""",file=fh)

            for name,line in self.branch.items():

                # create nodes for missing nodes
                while not line['sub_1'] or line['sub_1'] in self.bus:
                    line['sub_1'] = hex(random.randint(0,2**64))[2:]
                print(f"""object bus
{{
    name "N_{line['sub_1']}";
}}""",file=fh)
                while not line['sub_2'] or line['sub_2'] in self.bus:
                    line['sub_2'] = hex(random.randint(0,2**64))[2:]
                print(f"""object bus
{{
    name "N_{line['sub_2']}";
}}""",file=fh)

                # write branch object
                print(f"""object branch
{{
    name "L_{name}";
    from "N_{line['sub_1']}";
    to "N_{line['sub_2']}";
}}""",file=fh)

def main(argv):
    """Main routine

    Arguments:

    * `argv`: command line arguments
    """
    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    location = {}
    output = None
    consolidate = None
    for key,value in args:

        if key in ["-h","--help","help"]:

            print(__doc__,file=sys.stdout)
            return app.E_OK

        elif key in ["-o","--output"] and 0 < len(value) < 2:

            output = value[0]

        elif key == "--consolidate" and len(value) == 1 and value[0] in ["county","state"]:

            consolidate = value[0]

        elif not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    model = Powerline(**location)
    model.write_glm(output)

    # normal termination condition
    return app.E_OK

def test():
    """Test routine"""

    def verify(name,value,expected):
        if value != expected and not expected is None:
            print(f"{name}({expected}!={value})",end=", ",file=sys.stderr)
            return False
        return True

    def test_state(state,n_bus=None,n_branch=None,n_link=None):
        print("Testing",state,end="... ",flush=True,file=sys.stderr)
        test = Powerline("US",state)
        global n_tested
        n_tested += 1
        a = verify(f"{state} busses",len(test.bus),n_bus)
        b = verify(f"{state} branches",len(test.branch),n_branch)
        c = verify(f"{state} links",len(test.link),n_link)
        if n_bus is None or n_branch is None or n_link is None:
            print(f"test_state({repr(state)},{len(test.bus)},{len(test.branch)},{len(test.link)})")
        if a and b and c:
            print("ok",file=sys.stderr)
        else:
            print("failed",file=sys.stderr)
            global n_failed
            n_failed += 1

    def test_county(state,county,n_bus=0,n_branch=0,n_link=0):
        print("Testing",county,state,end="... ",flush=True,file=sys.stderr)
        test = Powerline("US",state,county)
        a = verify(f"{county} {state} busses",len(test.bus),n_bus)
        b = verify(f"{county} {state} branches",len(test.branch),n_branch)
        c = verify(f"{county} {state} links",len(test.link),n_link)
        global n_tested
        n_tested += 1
        if n_bus is None or n_branch is None or n_link is None:
            print(f"test_county({repr(state)},{repr(county)},{len(test.bus)},{len(test.branch)},{len(test.link)})")
        if a and b and c:
            print("ok",file=sys.stderr)
        else:
            print("failed",file=sys.stderr)
            global n_failed
            n_failed += 1

    def test_consolidated_state(state,n_link=0):
        print("Testing consolidated",state,end="... ",flush=True,file=sys.stderr)
        test = Powerline("US",state)
        a = verify(f"consolidated {state} busses",len(test.bus),1)
        b = verify(f"consolidated {state} branches",len(test.branch),0)
        c = verify(f"consolidated {state} links",len(test.link),n_link)
        global n_tested
        n_tested += 1
        if n_link is None:
            print(f"test_consolidated_state({repr(state)},{len(test.link)})")            
        if a and b and c:
            print("ok",file=sys.stderr)
        else:
            print("failed",file=sys.stderr)
            global n_failed
            n_failed += 1

    def test_consolidated_county(state,county,n_link=0):
        print("Testing consolidated",county,state,end="... ",flush=True,file=sys.stderr)
        test = Powerline("US",state,county)
        a = verify(f"consolidated {county} {state} busses",len(test.bus),1)
        b = verify(f"consolidated {county} {state} branches",len(test.branch),0)
        c = verify(f"consolidated {county} {state} links",len(test.link),n_link)
        global n_tested
        n_tested += 1
        if a and b and c:
            print("ok",file=sys.stderr)
        else:
            print("failed",file=sys.stderr)
            global n_failed
            n_failed += 1

    test_consolidated_state("WA")
    test_consolidated_county("WA","Pierce",154)
    test_county("WA","Snohomish",123,130,78)

    from gridlabd.census import Census, FIPS_STATES
    expected = {
        "ID": (813,854,411),
        "CA": (3722,2649,1445),
        "NY": (2761,2833,1130),
    }
    for state in FIPS_STATES:
        if state in expected:
            test_state(state,*expected[state])
        else:
            test_state(state)


    return n_failed,n_tested

if __name__ == "__main__":

    if not sys.argv[0]:

        n_tested = 0
        n_failed = 0
        app.test(test,__file__)

    else:

        app.run(main)
