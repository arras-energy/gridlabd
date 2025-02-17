"""Census data access"""

import re
import pandas as pd

CENSUS_DATA = "https://www2.census.gov/geo/docs/reference"

FIPS_STATES = pd.read_csv(f"{CENSUS_DATA}/state.txt",
    delimiter="|",
    index_col=[1],
    usecols=[0,1,2],
    header=0,
    names=["fips","state","name"]
    ).to_dict('index')

class CensusError(Exception):
    pass

class Census:

    cache = {}
    def __init__(self,state,county=None):
        if state not in FIPS_STATES:
            raise CensusError(f"state {repr(state)} not found")
        file = f"""st{int(FIPS_STATES[state]["fips"]):02.0f}_{state.lower()}_cou.txt"""
        if file in self.cache:
            result = self.cache[file]
        else:
            self.cache[file] = result = pd.read_csv(f"{CENSUS_DATA}/codes/files/{file}",
                usecols=[1,2,3],
                names=["state","county","name"],
                header=None,
                converters={
                    "state" : lambda x: f"{int(x):02.0f}",
                    "county" : lambda x: f"{int(x):03.0f}",
                },
                index_col=[2]
            )

        # compute the g-code used by NREL resstock and comstock
        result["gcode"] = [f"g{x}0{y}0" for x,y in zip(result["state"],result["county"])]
        result = result.to_dict("index")
        self.args = {"state":state,"county":county}
        if county is None:
            self.data = result
        else:
            self.data =  {x:y for x,y in result.items() if re.match(county,x)}

    def __str__(self):

        return str(self.data)

    def __repr__(self):

        args = [f"{x}={repr(y)}" for x,y in self.args.items()]
        return f"Census({','.join(args)})"

    def length(self):

        return len(self.data)

    def list(self):

        return list(self.data)

    def dict(self):

        return self.data

    def __getitem__(self,name):

        return self.data[name]

if __name__ == "__main__":

    result = Census("CA","San Mateo")
    print("str() =",result)
    print("repr() =",repr(result))
    print("length() =",result.length())
    print("list() =",result.list())
    print("dict() =",result.dict())
    print("__getitem__('San Mateo County') =",result["San Mateo County"])

