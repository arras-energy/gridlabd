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

TIMEZONES = {
    "01": "CST+6CDT", # AL
    "02": "AKST+9", # AK
    "04": "MST+7", # AZ
    "05": "CST+6CDT", # AR
    "06": "PST+8PDT", # CA
    "08": "MST+7MDT", # CO
    "09": "EST+5EDT", # CT
    "10": "EST+5EDT", # DE
    "11": "EST+5EDT", # DC
    "12": "EST+5EDT", # FL
    "13": "EST+5EDT", # GA
    "15": "HST+10", # HI
    "16": "MST+7MDT", # ID
    "17": "CST+6CDT", # IL
    "18": "EST+5EDT", # IN
    "19": "CST+6CDT", # IA
    "20": "CST+6CDT", # KS
    "21": "CST+6CDT", # KY
    "22": "CST+6CDT", # LA
    "23": "EST+5EDT", # ME
    "24": "EST+5EDT", # MD
    "25": "EST+5EDT", # MA
    "26": "EST+5EDT", # MI
    "27": "CST+6CDT", # MN
    "28": "CST+6CDT", # MS
    "29": "CST+6CDT", # MO
    "30": "MST+7MDT", # MT
    "31": "CST+6CDT", # NE
    "32": "MST+7MDT", # NV
    "33": "EST+5EDT", # NH
    "34": "EST+5EDT", # NJ
    "35": "MST+7MDT", # NM
    "36": "EST+5EDT", # NY
    "37": "EST+5EDT", # NC
    "38": "CST+6CDT", # ND
    "39": "EST+5EDT", # OH
    "40": "CST+6CDT", # OK
    "41": "PST+8PDT", # OR
    "42": "EST+5EDT", # PA
    "44": "EST+5EDT", # RI
    "45": "EST+5EDT", # SC
    "46": "CST+6CDT", # SD
    "47": "CST+6CDT", # TN
    "48": "CST+6CDT", # TX
    "49": "MST+7MDT", # UT
    "50": "EST+5EDT", # VT
    "51": "EST+5EDT", # VA
    "53": "PST+8PDT", # WA
    "54": "EST+5EDT", # WV
    "55": "CST+6CDT", # WI
    "56": "MST+7MDT", # WY
    "60": "SST+11", # AS
    "66": "CHST+10", # GU
    "69": "CHST+10", # MP
    "72": "AST+4", # PR
    "74": "CHST+10", # UM
    "78": "AST+4", # VI
}

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
        result["tzspec"] = [TIMEZONES[x] for x in result["state"]]
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

