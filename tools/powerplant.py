"""Powerplant data tool

Syntax: `gridlabd powerplant COUNTRY STATE COUNTY [OPTIONS ...]`

Options:

* `-o|--output=FILENAME`: specify GLM or CSV output to FILENAME

Description:

The `powerplant` tool read the HIFLD database for powerplant data in the
specified COUNTY, STATE, and COUNTY.

Example:

The following write the powerplant data for Grant County WA to `stdout`:

~~~
gridlabd powerplant US WA Grant
~~~

See Also:

* [[/Tools/Framework]]
* [HIFLD powerplant data repository](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::power-plants-2)

"""

import os
import sys
import json
import requests
import pandas as pd
import gridlabd.framework as app
import gridlabd.census as census

URL = "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Plants_gdb/FeatureServer/0/query?where=COUNTYFIPS%20%3D%20'{COUNTYFIPS}'&outFields={OUTFIELDS}&outSR=4326&f=json"
OUTFIELDS = "*"
CONVERTERS = {
    "plant_code": int,
    "name": lambda x:x.title(),
    "address": lambda x: x.title(),
    "city":  lambda x: x.title(),
    "state": lambda x: x.upper(),
    "zip": int,
    "telephone": lambda x: (x if x != "NOT AVAILABLE" else ""),
    "type": lambda x: (x.upper() if x != "NOT AVAILABLE" else ""),
    "status": lambda x: (x if x != "NOT AVAILABLE" else ""),
    "county": lambda x: x.title(),
    "countyfips": int,
    "country": lambda x: ("US" if x == "USA" else x.upper()),
    "latitude": float,
    "longitude": float,
    "naics_code": int,
    "naics_desc": lambda x: x.title(),
    "oper_cap": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "winter_cap": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "summer_cap": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "plan_cap": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "retire_cap": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "gen_units": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "plan_unit": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "retir_unit": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'),
    "prim_fuel": lambda x: (x if x != "NOT AVAILABLE" else ""),
    "sec_fuel": lambda x: (x if x != "NOT AVAILABLE" else ""),
    "coal_used": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'), 
    "ngas_used": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'), 
    "oil_used": lambda x: float(x) if x != "NONE" and float(x) >= 0 else float('nan'), 
    "net_gen": float,
    "cap_factor": float,
    "sub_1": lambda x: (x if x != "NOT AVAILABLE" else ""),
    "sub_2": lambda x: (x if x != "NOT AVAILABLE" else ""),
    "lines": lambda x: float(x) if x != "NOT AVAILABLE" else float('nan'),
    "source_lat": lambda x: float(x) if -90 <= float(x) <= 90 else float('nan'), 
    "sourc_long": lambda x: float(x) if -180 <= float(x) <= 180 else float('nan'), 
}

class PowerPlantError(Exception):
    """Powerplant exception"""

class Powerplant:
    """Powerplant class"""
    def __init__(self,country:str,state:str,county:str,planttype:str=None):
        """Create a powerplant dataset

        Arguments:

        * `country`: only `'US'` is supported

        * `state`: state name (abbreviated)

        * `county`: country name regex pattern (e.g., starting with)

        * `planttype`: plant type filter
        """
        if country != "US":
            raise PowerplantError("only US powerplant supported")

        info = census.Census(country,state,county)
        if not 0 < info.length() < 2:
            raise PowerplantError("exactly one county must match county name")
        county_name = info.list()[0]

        cachedir = os.path.join(os.environ["GLD_ETC"],".cache/powerplant")
        os.makedirs(cachedir,exist_ok=True)
        cachefile = os.path.join(cachedir,f"{country}_{state}_{county_name.replace(' ','')}.csv")
        if not os.path.exists(cachefile):
            data = json.loads(requests.get(URL.format(COUNTYFIPS=info.data[county_name]["pcode"],OUTFIELDS=OUTFIELDS)).content)
            with open(cachefile,"w") as fh:
                header = None
                for item in [x["attributes"] for x in data['features']]:
                    if not header:
                        header = list(item)
                        print(",".join([x.lower() for x in header]),file=fh)
                    print(",".join([str(item[x]) for x in header]),file=fh)
        self.data = pd.read_csv(cachefile,
            usecols=list(CONVERTERS),
            converters=CONVERTERS,
            index_col=["plant_code"]
            ).sort_index()

    def to_glm(self,fh:str=sys.stdout):
        """Generate GLM file from powerplant data

        Arguments:

        * `fh`: file name or file handle
        """
        converters = {
            "name": lambda x: x.upper().replace(" ","_"),
            "address": str,
            "city": str,
            "state": str,
            "zip": int,
            "telephone": str,
            "type": lambda x: x.upper().replace(" ","_"),
            "status": lambda x: x.upper().replace(" ","_"),
            "county": str,
            "countyfips": int,
            "country": lambda x: x.upper().replace(" ","_"),
            "latitude": lambda x: round(float(x),9),
            "longitude": lambda x: round(float(x),9),
            "naics_code": int,
            "naics_desc": lambda x: x.title(),
            "oper_cap": float,
            "summer_cap": float,
            "winter_cap": float,
            "plan_cap": float,
            "retire_cap": float,
            "gen_units": float,
            "plan_unit": float,
            "retir_unit": float,
            "prim_fuel": lambda x: x.upper().replace(" ","_"),
            "sec_fuel": lambda x: x.upper().replace(" ","_"),
            "coal_used": float,
            "ngas_used": float,
            "oil_used": float,
            "net_gen": float,
            "cap_factor": float,
            "sub_1": str,
            "sub_2": str,
            "lines": float,
            "source_lat": lambda x: round(float(x),9),
            "sourc_long": lambda x: round(float(x),9),
        }
        def convert(x,y):
            if isinstance(y,str):
                return f'{x} "{converters[x](y)}"'
            else:
                return f'{x} {converters[x](y)}'
        if isinstance(fh,str):
            fh = open(fh,"w")
        print("""class powerplant
{
    int32 plant_id;
    char256 address;
    char32 city;
    char8 state;
    int32 zip;
    char32 telephone;
    char256 type;
    char8 status;
    char32 county;
    int32 countyfips;
    char8 country;
    int32 naics_code;
    char256 naics_desc;
    double oper_cap[MW];
    double summer_cap[MW];
    double winter_cap[MW];
    double plan_cap[MW];
    double retire_cap[MW];
    double gen_units;
    double plan_unit;
    double retir_unit;
    char8 prim_fuel;
    char8 sec_fuel;
    double coal_used[ton];
    double ngas_used[ccf];
    double oil_used[gal];
    double net_gen[MW];
    double cap_factor[pu];
    char256 sub_1;
    char256 sub_2;
    double lines;
    double source_lat[deg];
    double sourc_long[deg];
}
""",file=fh)             
        for name,data in self.data.to_dict('index').items():
            properties = "\n".join([f'    {convert(x,y)};' for x,y in data.items() if y])
            print(f"""object powerplant
{{
    plant_id {name};
{properties}
}}""",file=fh)

def main(argv):
    """Main process

    Arguments:

    * `argv`: command line argument list

    Returns:

    * `int`: exit code (see `framework.E_*` codes)
    """
    if len(argv) == 1:
        
        app.syntax(__doc__)
        return app.E_SYNTAX

    args = app.read_stdargs(argv)

    location = {}
    output = None
    for key,value in args:

        if key in ["-h","--help","help"] and len(value) == 0:
            print(__doc__,file=sys.stdout)
            return app.E_OK

        elif key in ["-o","--output"] and 0 < len(value) < 2:

            output = value[0]

        elif not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

        else:

            app.error(f"'{key}={','.join(value) if value else 'None'}' is invalid")
            return app.E_INVALID

    result = Powerplant(**location)
    if isinstance(output,str):
        if output.endswith(".glm"):
            result.to_glm(output)
            return app.E_OK
        elif output.endswith(".csv"):
            result.data.to_csv(output,index=True,header=True)
            return app.E_OK
    elif output is None:
        result.data.to_csv(sys.stdout,index=True,header=True)
        return app.E_OK

    app.error(f"output to '{output}' is not possible")

    return app.E_INVALID

def test():
    """Test procedure

    Returns:

    * `int,int`: number failed and number tested
    """
    n_tested,n_failed = 0,0
    try:
        n_tested += 1
        plants = Powerplant("US","WA","Grant")
        assert len(plants.data) == 6, "incorrect number of powerplants in Grant County, WA"
    except:
        n_failed += 1
    return n_failed,n_tested

if __name__ == "__main__":

    if not sys.argv[0]:

        app.test(test,__file__)

    else:

        app.run(main)
