import os
import sys
import geojson as geo
import pandas as pd
import gridlabd.resource as resource
import requests

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

cachedir = os.path.join(os.environ['GLD_ETC'],".cache","powerline")
os.makedirs(cachedir,exist_ok=True)
cachename = os.path.join(cachedir,"powerlines.csv.gz")

if not os.path.exists(cachename):

    print("Downloading data",end="...",flush=True,file=sys.stderr)
    # data = requests.get("https://s3.us-east-2.amazonaws.com/infrastructure.arras.energy/US/powerlines.geojson").content
    data = resource.cache(name="infrastructure",index="powerlines.geojson")
    data = geo.loads(data)
    print("ok",flush=True,file=sys.stderr)

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
    print(f"{len(rows)} powerlines found",file=sys.stderr)
    data = pd.DataFrame(rows,columns=header,dtype=str)
    print(f"Saving to {cachename}",end="...",file=sys.stderr)
    data.set_index("ID").sort_index().to_csv(cachename,header=True,index=True)
    print("ok",file=sys.stderr,flush=True)
    del data

lines = pd.read_csv(cachename,index_col="ID",converters=CONVERTERS)
lines.drop([x for x in lines.columns if x not in CONVERTERS],inplace=True,axis=1)
lines.columns = [x.lower() for x in lines.columns]
lines.index.name = "name"

# pd.options.display.max_columns = None
# pd.options.display.width=None
# print(data)

nodes = list(set(list(lines["sub_1"])+list(lines["sub_2"])))

with open("/tmp/test.glm","w") as fh:
    print("module pypower;",file=fh)
    # print("class bus\n{\n}",file=fh)
    # print("class branch\n{\n    object from;\n    object to;\n}",file=fh)
    for node in nodes:
        print(f"""object bus
{{
    name "N_{node}";
}}""",file=fh)

    for name,line in lines.iterrows():
        if line['sub_1'] and line['sub_2']:
            print(f"""object branch
{{
    name "L_{name}";
    from "N_{line['sub_1']}";
    to "N_{line['sub_2']}";
}}""",file=fh)
        else:
            print(f"WARNING [powerline]: branch 'L_{name}' is missing properties: {', '.join([x for x in ['sub_1','sub_2'] if not line[x]])} not found",file=sys.stderr)

