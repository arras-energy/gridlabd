"""Powerline data tool

Syntax: `gridlabd powerline COUNTRY [STATE [COUNTY]] [OPTIONS ...]

Options:

* `-o|--output=FILENAME`: output network model to FILENAME

Description:

The `powerline` tool reads the HIFLD transmission line data repository and
generates a network model for the specified region.  The output FILENAME may
a `.glm` or `.json` file.  

Example:

See also:

* [[/Tools/Powerplant]]
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

class Network:

    resource = gr.Resource()

    def __init__(self):

        cachedir = os.path.join(os.environ['GLD_ETC'],".cache","powerline")
        os.makedirs(cachedir,exist_ok=True)
        cachename = os.path.join(cachedir,"powerlines.csv.gz")

        if not os.path.exists(cachename):

            # print("Downloading data",end="...",flush=True,file=sys.stderr)
            # data = requests.get("https://s3.us-east-2.amazonaws.com/infrastructure.arras.energy/US/powerlines.geojson").content
            file = self.resource.cache(name="infrastructure",index="powerlines.geojson.gz")
            # print("cache from",file,file=sys.stderr,flush=True)
            data = gj.loads(gzip.decompress(open(file,"rb").read()))
            # print("ok",flush=True,file=sys.stderr)

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
                    # TODO
                n += 1
            # print(f"{len(rows)} powerlines found",file=sys.stderr)
            data = pd.DataFrame(rows,columns=header,dtype=str)
            # print(f"Saving to {cachename}",end="...",file=sys.stderr)
            data.set_index("ID").sort_index().to_csv(cachename,header=True,index=True)
            # print("ok",file=sys.stderr,flush=True)
            del data

        lines = pd.read_csv(cachename,index_col="ID",converters=CONVERTERS)
        lines.drop([x for x in lines.columns if x not in CONVERTERS],inplace=True,axis=1)
        lines.columns = [x.lower() for x in lines.columns]
        lines.index.name = "name"

        self.branch = lines.to_dict('index')
        substations = substation.Substation("US").to_dict()
        self.bus = {x:(substations[x] if x in substations else {}) for x in set(list(lines["sub_1"])+list(lines["sub_2"]))}

    def write_glm(self,outfile:str):

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

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    location = {}
    output = None
    for key,value in args:

        if key in ["-h","--help","help"]:

            print(__doc__,file=sys.stdout)
            return app.E_OK

        elif key in ["-o","--output"] and 0 < len(value) < 2:

            output = value[0]

        elif not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement your code here
    model = Network()
    model.write_glm(output)

    # normal termination condition
    return app.E_OK

def test():

    test = Network()
    n_tested = len(test.bus) + len(test.branch)
    n_failed = 0
    if len(test.bus) != 67801:
        print(f"TEST: incorrect number of busses, expected 67801, got {len(test.bus)}")
        n_failed += 1
    if len(test.branch) != 94216:
        print(f"TEST: incorrect number of branches, expected 94216, got {len(test.branch)}")
        n_failed += 1
    return n_failed,n_tested

if __name__ == "__main__":

    if not sys.argv[0]:

        app.test(test,__file__)

    else:

        app.run(main)
