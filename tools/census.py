"""Census data access

Syntax: gridlabd census COUNTRY STATE [COUNTY]

The census tool obtains Census Bureau data about counties

Data obtained include the following:

* `state`: state FIPS code

* `county`: county FIPS code

* `gcode`: NREL county $g$-code

* `pgode`: HIFLD county $p$-code

* `tzspec`: timezone specification for state and county

* `population_{year}`: population for the indicated year

Caveats:

The value of `STATE` must be the two character abbreviation, e.g., `CA`.  The
value `COUNTY` may be a county name or a `regex` pattern to match multiple
counties.  The defaults value for `COUNTY` is `.*`, which will match all
counties in the state.

Some counties have multiple timezones. The `tzspec` specification for counties
that have more than one timezone is given for the more populous/larger portion of
the county. The following counties are affected by this issue:

* Florida: Gulf
* Idaho: Idaho
* Nebraska: Cherry
* North Dakota: McKenzie, Dunn, Sioux
* Oregon: Malheur
* South Dakota: Cherry

Example:



See also:

* [[/Tools/Framework]]
"""

import os
import sys
import re
import pandas as pd
import gridlabd.framework as app
import urllib

CACHEDIR = os.path.join(os.environ["GLD_ETC"],".cache/census")
CENSUS_DATA = "https://www2.census.gov/geo/docs/reference"
POPULATION_DATA = {
    "2000" : "https://www2.census.gov/geo/docs/reference/cenpop2000/county/cou_{fips}_{state}.txt",
    "2010" : "https://www2.census.gov/geo/docs/reference/cenpop2010/county/CenPop2010_Mean_CO{fips}.txt",
    "2020" : "https://www2.census.gov/geo/docs/reference/cenpop2020/county/CenPop2020_Mean_CO{fips}.txt",
}
POPULATION_SPEC = {
    "2000" : {
        "header": None,
        "usecols": [0,1,3],
        "index_col": [0,1],
        "encoding" : "utf-8",
        "names": ["state","county","population"],
        "converters": {
            "state" : lambda x: f"{int(x):02.0f}",
            "county" : lambda x: f"{int(x):03.0f}",
            "population" : float,
        },
    },
    "2010" : {
        "header": 0,
        "usecols": [0,1,4],
        "index_col": [0,1],
        "encoding" : "utf-8",
        "names": ["state","county","population"],
        "converters": {
            "state" : lambda x: f"{int(x):02.0f}",
            "county" : lambda x: f"{int(x):03.0f}",
            "population" : float,
        },
    },
    "2020" : {
        "header": 0,
        "usecols": [0,1,4],
        "index_col": [0,1],
        "encoding" : "utf-8",
        "names": ["state","county","population"],
        "converters": {
            "state" : lambda x: f"{int(x):02.0f}",
            "county" : lambda x: f"{int(x):03.0f}",
            "population" : float,
        },
    },
}

def strict_ascii(text):
    return ''.join([NONASCII[x] if x in NONASCII else x for x in text])

def get_cache(file,url,cacheargs={},**kwargs):
    os.makedirs(CACHEDIR,exist_ok=True)
    path = os.path.join(CACHEDIR,file)
    if not os.path.exists(path):
        pd.read_csv(url,**kwargs).to_csv(path,index=True,header=True)
    return pd.read_csv(path,**cacheargs)

FIPS_STATES = get_cache(file="states.txt",
        url=f"{CENSUS_DATA}/state.txt",
        cacheargs={
            "index_col":[0],
            "header": 0,
        },
        delimiter="|",
        index_col=[1],
        usecols=[0,1,2],
        header=0,
        names=["fips","state","name"],
    ).to_dict('index')


TIMEZONES = {
    "01": "CST+6CDT", # AL
    "02": "AKST+9", # AK
    "02016": "HST+10HDT", # AK Aleutians West Census Area 
    "04": "MST+7", # AZ all mountain countries without summer time
    "04001": "MST+7MDT", # AZ Apache County
    "04017": "MST+7MDT", # AZ Navaho County
    "05": "CST+6CDT", # AR
    "06": "PST+8PDT", # CA
    "08": "MST+7MDT", # CO
    "09": "EST+5EDT", # CT
    "10": "EST+5EDT", # DE
    "11": "EST+5EDT", # DC
    "12": "EST+5EDT", # FL all eastern counties 
    "12005": "CST+6CDT", # FL Bay County
    "12013": "CST+6CDT", # FL Calhoun County
    "12033": "CST+6CDT", # FL Escambia County
    "12045": "EST+5EDT", # FL Gulf County (divided)
    "12059": "CST+6CDT", # FL Holmes County
    "12063": "CST+6CDT", # FL Jackson County
    "12091": "CST+6CDT", # FL Okaloosa County
    "12113": "CST+6CDT", # FL Santa Rosa County
    "12131": "CST+6CDT", # FL Walton County
    "12133": "CST+6CDT", # FL Washington County
    "13": "EST+5EDT", # GA
    "15": "HST+10", # HI
    "16": "MST+7MDT", # ID all mountain counties
    "16009": "PST+8PDT", # ID Benewah County
    "16017": "PST+8PDT", # ID Bonner County
    "16021": "PST+8PDT", # ID Boundary County
    "16035": "PST+8PDT", # ID Clearwater County
    "16049": "MST+7MDT", # ID Idaho County (divided)
    "16055": "PST+8PDT", # ID Kootenai County
    "16057": "PST+8PDT", # ID Latah County
    "16061": "PST+8PDT", # ID Lewis County
    "16069": "PST+8PDT", # ID Nez Perce County
    "16079": "PST+8PDT", # ID Shoshone County
    "17": "CST+6CDT", # IL
    "18": "EST+5EDT", # IN all eastern counties
    "18051" : "CST+6CDT", # IN Gibson County
    "18073" : "CST+6CDT", # IN Jasper County
    "18089" : "CST+6CDT", # IN Lake County
    "18091" : "CST+6CDT", # IN LaPorte County
    "18111" : "CST+6CDT", # IN Newton County
    "18123" : "CST+6CDT", # IN Perry County
    "18127" : "CST+6CDT", # IN Porter County
    "18129" : "CST+6CDT", # IN Posey County
    "18147" : "CST+6CDT", # IN Spencer County
    "18149" : "CST+6CDT", # IN Starke County
    "18163" : "CST+6CDT", # IN Vanderburg County
    "18173" : "CST+6CDT", # IN Warrick County
    "19": "CST+6CDT", # IA
    "20": "CST+6CDT", # KS all eastern counties
    "20071": "MST+7MDT", # KS Greeley County
    "20": "MST+7MDT", # KS Hamilton County
    "20": "MST+7MDT", # KS Sherman County
    "20": "MST+7MDT", # KS Wallace County
    "21": "EST+5EDT", # KY all eastern counties
    "21001": "CST+6CDT", # KY Adair County
    "21003": "CST+6CDT", # KY Allen County
    "21007": "CST+6CDT", # KY Ballard County
    "21009": "CST+6CDT", # KY Barren County
    "21027": "CST+6CDT", # KY Breckinridge County
    "21031": "CST+6CDT", # KY Butler County
    "21033": "CST+6CDT", # KY Caldwell County
    "21035": "CST+6CDT", # KY Calloway County
    "21039": "CST+6CDT", # KY Carlisle County
    "21047": "CST+6CDT", # KY Christian County
    "21053": "CST+6CDT", # KY Clinton County
    "21055": "CST+6CDT", # KY Crittenden County
    "21057": "CST+6CDT", # KY Cumberland County
    "21059": "CST+6CDT", # KY Daviess County
    "21061": "CST+6CDT", # KY Edmonson County
    "21075": "CST+6CDT", # KY Fulton County
    "21083": "CST+6CDT", # KY Graves County
    "21085": "CST+6CDT", # KY Grayson County
    "21087": "CST+6CDT", # KY Green County
    "21091": "CST+6CDT", # KY Hancock County
    "21099": "CST+6CDT", # KY Hart County
    "21101": "CST+6CDT", # KY Henderson County
    "21105": "CST+6CDT", # KY Hickman County
    "21107": "CST+6CDT", # KY Hopkins County
    "21139": "CST+6CDT", # KY Livingston County
    "21141": "CST+6CDT", # KY Logan County
    "21143": "CST+6CDT", # KY Lyon County
    "21157": "CST+6CDT", # KY Marshall County
    "21145": "CST+6CDT", # KY McCracken County
    "21149": "CST+6CDT", # KY McLean County
    "21169": "CST+6CDT", # KY Metcalfe County
    "21171": "CST+6CDT", # KY Monroe County
    "21177": "CST+6CDT", # KY Muhlenberg County
    "21183": "CST+6CDT", # KY Ohio County
    "21207": "CST+6CDT", # KY Russell County
    "21213": "CST+6CDT", # KY Simpson County
    "21219": "CST+6CDT", # KY Todd County
    "21221": "CST+6CDT", # KY Trigg County
    "21225": "CST+6CDT", # KY Union County
    "21227": "CST+6CDT", # KY Warren County
    "21233": "CST+6CDT", # KY Webster County
    "22": "CST+6CDT", # LA
    "23": "EST+5EDT", # ME
    "24": "EST+5EDT", # MD
    "25": "EST+5EDT", # MA
    "26": "EST+5EDT", # MI all eastern counties
    "26043": "CST+6CDT", # MI Dickenson County
    "26053": "CST+6CDT", # MI Gogebic County
    "26071": "CST+6CDT", # MI Iron County
    "26109": "CST+6CDT", # MI Menominee County
    "27": "CST+6CDT", # MN
    "28": "CST+6CDT", # MS
    "29": "CST+6CDT", # MO
    "30": "MST+7MDT", # MT
    "31": "CST+6CDT", # NE all central counties
    "31005": "MST+7MDT", # NE Arthur County
    "31007": "MST+7MDT", # NE Banner County
    "31029": "MST+7MDT", # NE Chase County
    "31031": "CST+6CDT", # NE Cherry County (divided)
    "31033": "MST+7MDT", # NE Cheyenne County
    "31045": "MST+7MDT", # NE Dawes County
    "31049": "MST+7MDT", # NE Deuel County
    "31057": "MST+7MDT", # NE Dundy County
    "31069": "MST+7MDT", # NE Garden County
    "31075": "MST+7MDT", # NE Grant County
    "31091": "MST+7MDT", # NE Hooker County
    "31101": "MST+7MDT", # NE Keith County
    "31105": "MST+7MDT", # NE Kimball County
    "31123": "MST+7MDT", # NE Morrill County
    "31135": "MST+7MDT", # NE Perkins County
    "31157": "MST+7MDT", # NE Scotts Bluff County
    "31161": "MST+7MDT", # NE Sheridan County
    "31165": "MST+7MDT", # NE Sioux County
    "32": "MST+7MDT", # NV
    "33": "EST+5EDT", # NH
    "34": "EST+5EDT", # NJ
    "35": "MST+7MDT", # NM
    "36": "EST+5EDT", # NY
    "37": "EST+5EDT", # NC
    "38": "CST+6CDT", # ND all central counties
    "38001": "MST+7MDT", # ND Adams County
    "38007": "MST+7MDT", # ND Billings County
    "38011": "MST+7MDT", # ND Bowman County
    "38025": "MST+7MDT", # ND Dunn County  (divided)
    "38033": "MST+7MDT", # ND Golden Valley County
    "38037": "MST+7MDT", # ND Grant County
    "38041": "MST+7MDT", # ND Hettinger County
    "38053": "MST+7MDT", # ND McKenzie (divided)
    "38085": "MST+7MDT", # ND Sioux County (divided)
    "38087": "MST+7MDT", # ND Slope County
    "38089": "MST+7MDT", # ND Stark County
    "39": "EST+5EDT", # OH
    "40": "CST+6CDT", # OK
    "41": "PST+8PDT", # OR all pacific counties
    "41045": "PST+8PDT", # OR Malheur County (divided)
    "42": "EST+5EDT", # PA
    "44": "EST+5EDT", # RI
    "45": "EST+5EDT", # SC
    "46": "CST+6CDT", # SD all central countries
    "46007": "MST+7MDT", # SD Bennett County
    "46019": "MST+7MDT", # SD Butte County
    "46031": "MST+7MDT", # SD Corson County
    "46033": "MST+7MDT", # SD Custer County
    "46041": "MST+7MDT", # SD Dewey County
    "46074": "MST+7MDT", # SD Fall River County
    "46055": "MST+7MDT", # SD Haakon County
    "46063": "MST+7MDT", # SD Harding County
    "46071": "MST+7MDT", # SD Jackson County
    "46081": "MST+7MDT", # SD Lawrence County
    "46093": "MST+7MDT", # SD Meade County
    "46102": "MST+7MDT", # SD Oglala Lakota County (after May 2015)
    "46103": "MST+7MDT", # SD Pennington County
    "46105": "MST+7MDT", # SD Perkins County
    "46113": "MST+7MDT", # SD Shannon County (before May 2015)
    "46117": "MST+7MDT", # SD Stanley County (divided)
    "46137": "MST+7MDT", # SD Ziebach County
    "47": "CST+6CDT", # TN all central counties
    "47001": "EST+5EDT", # TN Anderson County
    "47009": "EST+5EDT", # TN Blount County
    "47011": "EST+5EDT", # TN Bradley County
    "47013": "EST+5EDT", # TN Campbell County
    "47019": "EST+5EDT", # TN Carter County
    "47025": "EST+5EDT", # TN Claiborne County
    "47029": "EST+5EDT", # TN Cocke County
    "47057": "EST+5EDT", # TN Grainger County
    "47059": "EST+5EDT", # TN Greene County
    "47063": "EST+5EDT", # TN Hamblen County
    "47065": "EST+5EDT", # TN Hamilton County
    "47067": "EST+5EDT", # TN Hancock County
    "47073": "EST+5EDT", # TN Hawkins County
    "47089": "EST+5EDT", # TN Jefferson County
    "47091": "EST+5EDT", # TN Johnson County
    "47093": "EST+5EDT", # TN Knox County
    "47105": "EST+5EDT", # TN Loudon County
    "47107": "EST+5EDT", # TN McMinn County
    "47121": "EST+5EDT", # TN Meigs County
    "47123": "EST+5EDT", # TN Monroe County
    "47129": "EST+5EDT", # TN Morgan County
    "47139": "EST+5EDT", # TN Polk County
    "47143": "EST+5EDT", # TN Rhea County
    "47145": "EST+5EDT", # TN Roane County
    "47151": "EST+5EDT", # TN Scott County
    "47155": "EST+5EDT", # TN Sevier County
    "47163": "EST+5EDT", # TN Sullivan County
    "47171": "EST+5EDT", # TN Unicoi County
    "47173": "EST+5EDT", # TN Union County
    "47179": "EST+5EDT", # TN Washington County
    "48": "CST+6CDT", # TX all central counties
    "48141": "MST+7MDT", # TX El Paso County
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

NONASCII = {
    "\xe1" : "a",
    "\xe9" : "e",
    "\xed" : "i",
    "\xf1" : "n",
    "\xf3" : "o",
    "\xfc" : "u",
    # may need to add other someday
}

class CensusError(Exception):
    """Census exception"""

class Census:
    """Census object class"""

    def __init__(self,country:str,state:str,county:str=None,on_error=app.warning):
        """Get census data

        Arguments:

        * `state`: State for which census data is downloaded

        * `county`: County regex for which census data is downloaded
        """
        if country != "US":
            raise CensusError("only US census data is available")

        if state not in FIPS_STATES:
            raise CensusError(f"state {repr(state)} not found")

        file = f"""counties_{int(FIPS_STATES[state]["fips"]):02.0f}_2020.txt"""
        result = get_cache(
                file=file,
                url=os.path.join(CENSUS_DATA,"codes2020","cou",f"""st{int(FIPS_STATES[state]["fips"]):02.0f}_{state.lower()}_cou2020.txt"""),
                cacheargs={
                    "header": 0,
                    "index_col": [0],
                    "dtype": str,
                },
                usecols=[1,2,4],
                names=["state","county","name"],
                header=0,
                delimiter="|",
                converters={
                    "state" : lambda x: f"{int(x):02.0f}",
                    "county" : lambda x: f"{int(x):03.0f}",
                    "name" : strict_ascii,
                },
                # index_col=[0,1],
            )

        # compute the g-code used by NREL resstock and comstock
        result["pcode"] = [f"{x}{y}" for x,y in zip(result["state"],result["county"])]
        result["gcode"] = [f"g{x}0{y}0" for x,y in zip(result["state"],result["county"])]
        result["tzspec"] = [TIMEZONES[x+y] if x+y in TIMEZONES else TIMEZONES[x] for x,y in zip(result["state"],result["county"])]
        result.reset_index(inplace=True)
        result.set_index(["state","county"],inplace=True)
        for year,url in POPULATION_DATA.items():
            file = f"""population_{FIPS_STATES[state]['fips']:02.0f}_{year}.txt"""
            url = url.format(fips=f"{FIPS_STATES[state]['fips']:02.0f}",state=state.lower())
            try:
                population = get_cache(file,url,
                    **POPULATION_SPEC[year],
                    )
                population["state"] = [f"{x:02.0f}" for x in population["state"]]
                population["county"] = [f"{x:03.0f}" for x in population["county"]]
                population.set_index(["state","county"],inplace=True,drop=True)
                result[f"population_{year}"] = population["population"]
            except urllib.error.HTTPError:
                on_error(f"{year} population data for {state} not available")

        result.reset_index(inplace=True)
        result.set_index("name",inplace=True)
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

def test(state:list=None,county:str=None) -> (int,int):
    """Test census data access

    Arguments:

    * `state`: states to test

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
        result = Census("US",st,county)
        for ct in result.list():
            expected = TIMEZONES[result[ct]["pcode"]] if result[ct]["pcode"] in TIMEZONES else TIMEZONES[result[ct]["state"]]
            if result[ct]["tzspec"] != expected:
                print(f"TEST FAILED: state={st} county={ct}, expected {expected} but got {result[ct]['tzspec']} instead",file=sys.stderr)
                n_failed += 1
            n_tested += 1

    return n_failed,n_tested

def main(argv:list[str]) -> int:

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    location = {}

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        # state/county info
        if not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

            if len(location) > 3:
                raise "only country, state, and county may be specified"

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement census code
    if len(location) == 0:
        raise CensusError("missing state/county specification")

    result = Census(**location)
    keys = list(result[list(result.data)[0]].keys())
    print("name,"+",".join(keys))
    for county,spec in result.dict().items():
        print(f"{county},{','.join([str(spec[x]) for x in keys])}")

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    if not sys.argv[0]:

        app.test(test,__file__)

    else:

        app.run(main)

