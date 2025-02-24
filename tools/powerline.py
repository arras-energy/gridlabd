"""Powerline data tool

Syntax: `gridlabd powerline COUNTRY [STATE [COUNTY]] [OPTIONS ...]

Options:

* `-o|--output=FILENAME`: output network model to FILENAME

* `--verify={syntax,solve}`: verify the model before saving

* `--reference=BUS`: specify the reference bus to start from (only connected
  nodes will be included)

Description:

The `powerline` tool reads the HIFLD transmission line data repository and
generates a network model for the specified region.  The output FILENAME may
a `.glm` or `.json` file.  If the `--verify=syntax` option is included, the
generated model is loaded in GridLAB-D using the compile option. If the
`--verify=solve` option is included, the network powerflow is solve for
initial conditions.

Example:

See also:

* [[/Tools/Powerplant]]
* [HIFLD transmission line data repository](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::transmission-lines/about)
"""
import os
import sys
import requests
import geojson as gj
import pandas as pd
import gridlabd.resource as gr
import gridlabd.framework as app

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

    def __init__(self):

        cachedir = os.path.join(os.environ['GLD_ETC'],".cache","powerline")
        os.makedirs(cachedir,exist_ok=True)
        cachename = os.path.join(cachedir,"powerlines.csv.gz")

        if not os.path.exists(cachename):

            # print("Downloading data",end="...",flush=True,file=sys.stderr)
            # data = requests.get("https://s3.us-east-2.amazonaws.com/infrastructure.arras.energy/US/powerlines.geojson").content
            file = gr.Resource().cache(name="infrastructure",index="powerlines.geojson")
            # print("cache from",file,file=sys.stderr,flush=True)
            data = gj.load(open(file,"r"))
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
        self.bus = {x:{} for x in set(list(lines["sub_1"])+list(lines["sub_2"]))}

    def write_glm(self,outfile:str):

        with open(outfile,"w") as fh:
            print("module pypower;",file=fh)
            for node in self.bus:
                print(f"""object bus
{{
    name "N_{node}";
}}""",file=fh)

            for name,line in self.branch.items():
                if line['sub_1'] and line['sub_2']:
                    print(f"""object branch
{{
    name "L_{name}";
    from "N_{line['sub_1']}";
    to "N_{line['sub_2']}";
}}""",file=fh)
                else:
                    print(f"WARNING [powerline]: branch 'L_{name}' is missing properties: {', '.join([x for x in ['sub_1','sub_2'] if not line[x]])} not found",file=sys.stderr)

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
