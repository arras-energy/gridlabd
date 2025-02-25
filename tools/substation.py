"""Substation tool

Syntax: gridlabd substation [COUNTRY[,...] [STATE[,...] [COUNTY[,...]]]] [OPTIONS ...]

Options:

* `--zipcode=ZIPCODE[,...]`: limit result to substations in ZIPCODE list

* `--status=STATUS[,...]`: limit result to substations having status in STATUS list

* `--fips=FIPS[,...]`: limit result to substations having county fips in FIPS list

* `--latitude=MIN,MAX`: limit result to substations in latitude range

* `--longitude=MIN,MAX`: limit result to substations in longitude range

* `--voltage=MIN,MAX`: limit result to substations in voltage range

* `--lines=MIN,MAX`: limit result to substations having lines in range

* `-o|--output=FILENAME`: output to GLM, CSV, or JSON file

Description:

The `substation` tool accesses substation data for the specified location and substation
characteristics.
"""
import os
import sys
import io
import gzip
import pandas as pd
import gridlabd.resource as gr
import gridlabd.framework as app
import gridlabd.encoding as encoding
import collections

def _asint(x,default=0):
    try:
        return int(x)
    except:
        return default

def _aslist(x):
    return x if type(x) in [list,tuple,set] else [x]

minmax = collections.namedtuple("minmax",["min","max"])
def _asminmax(x):
    if type(x) is minmax:
        return x
    return minmax(min(x),max(x))

CONVERTERS = {
    "NAME": lambda x: encoding.strict_ascii(x).replace(" ","_") if x not in ["NOT AVAILABLE"] else "UNKNOWN",
    "CITY": lambda x: encoding.strict_ascii(x).title() if x not in ["NOT AVAILABLE"] else "",
    "ZIP": _asint,
    "STATE": lambda x: x[:2].upper(),
    "TYPE": lambda x: x.upper().replace(" ","_") if x not in ["NOT AVAILABLE"] else "UNKNOWN",
    "STATUS": lambda x: x.upper().replace(" ","_") if x not in ["NOT AVAILABLE"] else "UNKNOWN",
    "COUNTY": lambda x: encoding.strict_ascii(x).title() if x not in ["NOT AVAILABLE"] else "",
    "COUNTYFIPS": lambda x: str(x) if x not in ["NOT AVAILABLE"] else "",
    "COUNTRY": lambda x: x[:2].upper(),
    "LATITUDE": lambda x: float(x) if x not in ["NOT AVAILABLE"] else float('nan'),
    "LONGITUDE": lambda x: float(x) if x not in ["NOT AVAILABLE"] else float('nan'),
    "LINES": _asint,
    "MAX_VOLT": lambda x: float(x) if x not in ["-999999","NOT AVAILABLE"] else float('nan'),
    "MIN_VOLT": lambda x: float(x) if x not in ["-999999","NOT AVAILABLE"] else float('nan'),
}

class SubstationError(Exception):
    """Substation exception handler"""

class Substation:
    """Substation data access class"""
    resource = gr.Resource()

    def __init__(self,
            country:str|list[str]=None,
            state:str|list[str]=None,
            county:str|list[str]=None,
            zipcode:int|list[int]=None,
            status:str|list[str]=None,
            fips:str|list[str]=None,
            latitude:minmax=None,
            longitude:minmax=None,
            voltage:minmax=None,
            lines:minmax=None,
            ):
        """Substation data object

        Arguments:

        * `country`: country filter
        
        * `state`: state filter
        
        * `county`: county filter
        
        * `zipcode`: zipcode filter
        
        * `status`: status filter
        
        * `fips`: fips filter
        
        * `latitude`: latitude range
        
        * `longitude`: longitude range
        
        * `voltage`: voltage range
        
        * `lines`: lines range
        """
        file = self.resource.cache(name="infrastructure",index="substations.csv.gz")
        buffer = io.StringIO(gzip.decompress(open(file,"rb").read()).decode("utf-8"))
        data = pd.read_csv(buffer,
            low_memory=False,
            na_values=["-999999","NOT AVAILABLE"],
            converters = CONVERTERS,
            )
        data.drop(data.loc[data["NAME"].duplicated()].index,inplace=True)
        data.set_index("NAME",inplace=True)
        data.index.name = "name"
        data.drop([x for x in data.columns if x not in CONVERTERS],axis=1,inplace=True)
        data.columns = [x.lower() for x in data.columns]
        if country:
            data.drop(data.loc[~data.country.isin(_aslist(country))].index,axis=0,inplace=True)
        if state:
            data.drop(data.loc[~data.state.isin(_aslist(state))].index,axis=0,inplace=True)
        if county:
            data.drop(data.loc[~data.county.isin(_aslist(county))].index,axis=0,inplace=True)
        if zipcode:
            data.drop(data.loc[~data.zip.isin(_aslist(zipcode))].index,axis=0,inplace=True)
        if status:
            data.drop(data.loc[~data.status.isin(_aslist(status))].index,axis=0,inplace=True)
        if fips:
            data.drop(data.loc[~data.countyfips.isin(_aslist(fips))].index,axis=0,inplace=True)
        if lines:
            lines = _asminmax(lines)
            data.drop(data.loc[data.lines<lines.min].index,axis=0,inplace=True)
            data.drop(data.loc[data.lines>lines.max].index,axis=0,inplace=True)
        if voltage:
            voltage = _asminmax(voltage)
            data.drop(data.loc[data.min_volt>voltage.max].index,axis=0,inplace=True)
            data.drop(data.loc[data.max_volt<voltage.min].index,axis=0,inplace=True)
        if latitude:
            latitude = _asminmax(latitude)
            data.drop(data.loc[data.latitude<latitude.min].index,axis=0,inplace=True)
            data.drop(data.loc[data.latitude>latitude.max].index,axis=0,inplace=True)
        if longitude:
            longitude = _asminmax(longitude)
            data.drop(data.loc[data.longitude<longitude.min].index,axis=0,inplace=True)
            data.drop(data.loc[data.longitude>longitude.max].index,axis=0,inplace=True)
        self.data = data

    def to_dict(self) -> dict:
        """Get data as dict"""
        return self.data.to_dict("index")

    def to_list(self) -> list:
        """Get data as list"""
        return list(self.data.index)

    def to_glm(self,filename:str=None) -> str:
        """Get data as glm"""
        result = "TODO"
        if not filename:
            return result
        with open(filename,"w") as fh:
            print("module pypower;",file=fh)
            for name,data in self.data.to_dict("index").items():
                properties = "\n".join([f"    {x} {y};" for x,y in data.items() if y])
                print(f"""object substation
{{
    name "{name}";
{properties}
}}""",file=fh)

    def to_csv(self,*args:list,**kwargs:dict) -> str|None:
        """Get data as csv"""
        return self.data.to_csv(*args,**kwargs)

    def to_json(self,*args:list,**kwargs:dict) -> str|None:
        """Get data as json"""
        return self.data.to_json(*args,**kwargs)

def main(argv:list[str]) -> int:
    """Main routine"""
    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    location = {}
    output = None
    strargs = {
        "status" : None,
        "fips" : None,
    }
    intargs = {
        "zipcode" : None,    
    }
    limargs = {
        "latitude" : None,
        "longitude" : None,
        "voltage" : None,
        "lines" : None,
    }
    for key,value in args:

        if key in ["-h","--help","help"]:
            
            print(__doc__,file=sys.stdout)
            return app.E_OK

        elif key in ["-o","--output"] and 0 < len(value) < 2:

            output = value[0]

        elif not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

        elif key.startswith("--") and key[2:] in strargs and len(value) > 0:

            strargs[key[2:]] = value

        elif key.startswith("--") and key[2:] in intargs and len(value) > 0:

            intargs[key[2:]] = [int(x) for x in value]

        elif key.startswith("--") and key[2:] in limargs and len(value) == 2:

            limargs[key[2:]] = [float(x) for x in value]

        elif key in ["-o","--output"] and len(value) == 1:

            output = value[0]

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    result = Substation(
        **location,
        **strargs,
        **intargs,
        **limargs,
        )
    if not output or output.endswith(".csv"):
        result.to_csv(open(output,"w") if output else sys.stdout)
    elif output.endswith(".glm"):
        result.to_glm(output)
    elif output.endswith(".json"):
        result.to_json(output,orient='index',indent=4)
    else:
        raise SubstationError(f"unsupported output file format (extension '{os.path.splitext(output)[1]}' not recognized)")


    # normal termination condition
    return app.E_OK

def test():
    """Test routine"""
    substation = Substation(
        country="US",
        state="WA",
        county="Snohomish",
        fips=["53061"],
        zipcode=[98270,98271],
        latitude=(48,48.1),
        longitude=(-122.1,-122.2),
        )
    return 0 if len(substation.data)==11 else 1,1

if __name__ == "__main__":

    if not sys.argv[0]:

        # # Developer use only to avoid build
        # sys.argv = [__file__,"US","WA","Snohomish","--fips=53061","--zipcode=98270,98271",
        #     "--latitude=48,48.1","--longitude=-122.1,-122.2","--output=/tmp/test.glm"]
        # app.run(main)

        app.test(test,__file__)

    else:

        app.run(main)
