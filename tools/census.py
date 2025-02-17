"""Census data access

Syntax: gridlabd census STATE [COUNTY]

The census tool obtains Census Bureau data about counties

Data obtained include the following:

* `state`: state FIPS code

* `county`: county FIPS code

* `gcode`: NREL county $g$-code

* `tzspec`: timezone specification for state and county

Caveats:

The value of `STATE` must be the two character abbreviation, e.g., `CA`.  The
value `COUNTY` may be a county name or a `regex` pattern to match multiple
counties.  The defaults value for `COUNTY` is `.*`, which will match all
counties in the state.

Some states have multiple timezones. The `tzspec` specification for states
that have more than one timezone is given for the more populous portion of
the state. 
"""

import os
import sys
import re
import pandas as pd
import gridlabd.framework as app

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
    """Census exception"""

class Census:
    """Census object class"""
    cache = {}
    def __init__(self,state:str,county:str=None,country="US"):
        """Get census data

        Arguments:

        * `state`: State for which census data is downloaded

        * `county`: County regex for which census data is downloaded
        """
        if country != "US":
            raise CensusError("only US census data is available")

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

    def length(self) -> int:
        """Get the number counties matching the county name given"""
        return len(self.data)

    def list(self) -> list:
        """Get a list of counties matching the county name given"""
        return list(self.data)

    def dict(self) -> dict:
        """Get a dict of the census data obtained"""
        return self.data

    def __getitem__(self,county:str) -> dict:
        """Get the census data for a county that matches"""
        return self.data[county]

def test(state:str=None,county:str=None) -> (int,int):
    """Test census data access

    Arguments:

    * `state`: state to test

    * `county`: county name pattern to test

    Returns:

    * `int`: failed tests

    * `int`: counties tested
    """
    if isinstance(state,str):
        state = [state]
    elif state is None:
        state = list(FIPS_STATES)
    n_tested = 0
    n_failed = 0
    for st in state:
        result = Census(st,county)
        for ct in result.list():
            if result[ct]["tzspec"] != TIMEZONES[result[ct]["state"]]:
                print(f"TEST FAILED: state={st} county={ct}",file=sys.stderr)
                n_failed += 1
            n_tested += 1

    return n_failed,n_tested

def main(argv:list[str]) -> int:

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    location = []

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        # state/county info
        if not key.startswith("-"):

            location.append(key)

            if len(location) > 2:
                raise CensusError("only state and county may be specified")

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement census code
    if len(location) == 0:
        raise CensusError("missing state/county specification")

    result = Census(*location)
    print(f"county,state,state_fips,county_fips,nrel_gcode,timezone")
    for county,spec in result.dict().items():
        print(f"{county},{location[0]},{spec['state']},{spec['county']},{spec['gcode']},{spec['tzspec']}")

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    if not sys.argv[0]:

        n,m = test()
        print(f"{os.path.basename(__file__)}: {m} tests, {n} failed")

    else:
        app.run(main)

