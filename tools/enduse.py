"""Access enduse load data from NREL

Syntax: gridlabd enduse COUNTRY STATE COUNTY [OPTIONS ...]

Options:

* `--local`: use local timezone

* `--electrification=ENDUSE:FRACTION[,...]`: specify enduse electrification

* `--list=FEATURE`: list of available features

* `--start`: set the start date (default is `2018-01-01 00:00:00 EST`)

* `--end`: set the end date (default is `2019-01-01 00:00:00 EST`)

* `--type=PATTERN[,...]`: specify the building type(s)

* `--model=FILENAME`: specify the GLM or JSON file to generate

* `--player=FILENAME`: specify the CSV file to generate

Description:

The `enduse` tool generates enduse load data for buildings at the specified
location.

Valid values for `FEATURE` are `sector`, `type`, `country`, `state`, `county`, and
`enduse`. If `state` is requests the COUNTRY must be specified. If `county` is 
requested, the COUNTRY and STATE must be specified.
"""

import os
import sys
import re
import json
import gridlabd.eia_recs as eia
import pandas as pd
import gridlabd.census as census
import gridlabd.framework as app

BUILDING_TYPE = {
    "residential" : {
        "MOBILE":"mobile_home",
        "MULTI_FAMILY_SMALL" : "multi-family_with_2_-_4_units",
        "MULTI_FAMILY_LARGE" : "multi-family_with_5plus_units",
        "SINGLE_FAMILY_ATTACHED" : "single-family_attached",
        "SINGLE_FAMILY_DETACHED" : "single-family_detached",
        },
    "commercial" : {
        "DINING_FULL": "fullservicerestaurant",
        "MEDICAL_LARGE": "hospital",
        "LODGING_LARGE": "largehotel",
        "OFFICE_LARGE": "largeoffice",
        "OFFICE_MEDIUM": "mediumoffice",
        "SMALLMEDICAL": "outpatient",
        "SCHOOL_SMALL": "primaryschool",
        "DINING_FAST": "quickservicerestaurant",
        "RETAIL_SMALL": "retailstandalone",
        "RETAIL_MEDIUM": "retailstripmall",
        "SCHOOL_LARGE": "secondaryschool",
        "LODGING_SMALL": "smallhotel",
        "WAREHOUSE": "warehouse",
    },
    "industrial": {},
    "agricultural": {},
    "transportation": {},
    }
SECTORS = list(BUILDING_TYPE.keys())
URL = {
    "residential": "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_{weather}_release_1/timeseries_aggregates/by_county/state%3D{state}/{gcode}-{type}.csv",
    "commercial": "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/comstock_{weather}_release_1/timeseries_aggregates/by_county/state%3D{state}/{gcode}-{type}.csv",
    "industrial": None,
    "agricultural": None,
    "tranportation" : None,
    }
CONVERTERS = {
    # value fields: name, format, electric
    "residential" : {
        "models_used": None,
        "units_represented": ["units",float, None],
        "out.electricity.bath_fan.energy_consumption": ["ventilation",float,True],
        "out.electricity.ceiling_fan.energy_consumption": ["ventilation",float,True],
        "out.electricity.clothes_dryer.energy_consumption": ["dryer",float,True],
        "out.electricity.clothes_washer.energy_consumption": ["washer",float,True],
        "out.electricity.cooking_range.energy_consumption": ["cooking",float,True],
        "out.electricity.cooling.energy_consumption": ["cooling",float,True],
        "out.electricity.dishwasher.energy_consumption": ["dishwasher",float,True],
        "out.electricity.ext_holiday_light.energy_consumption": ["lights",float,True],
        "out.electricity.exterior_lighting.energy_consumption": ["lights",float,True],
        "out.electricity.extra_refrigerator.energy_consumption": ["refrigerator",float,True],
        "out.electricity.fans_cooling.energy_consumption": ["ventilation",float,True],
        "out.electricity.fans_heating.energy_consumption": ["ventilation",float,True],
        "out.electricity.freezer.energy_consumption": ["freezer",float,True],
        "out.electricity.garage_lighting.energy_consumption": ["lights",float,True],
        "out.electricity.heating.energy_consumption": ["heating",float,True],
        "out.electricity.heating_supplement.energy_consumption": ["heating",float,True],
        "out.electricity.hot_tub_heater.energy_consumption": ["heating",float,True],
        "out.electricity.hot_tub_pump.energy_consumption": ["heating",float,True],
        "out.electricity.house_fan.energy_consumption": ["ventilation",float,True],
        "out.electricity.interior_lighting.energy_consumption": ["lights",float,True],
        "out.electricity.plug_loads.energy_consumption": ["plugs",float,True],
        "out.electricity.pool_heater.energy_consumption": ["heating",float,True],
        "out.electricity.pool_pump.energy_consumption": ["heating",float,True],
        "out.electricity.pumps_cooling.energy_consumption": ["cooling",float,True],
        "out.electricity.pumps_heating.energy_consumption": ["heating",float,True],
        "out.electricity.pv.energy_consumption": ["solar",float,True],
        "out.electricity.range_fan.energy_consumption": ["ventilation",float,True],
        "out.electricity.recirc_pump.energy_consumption": ["other",float,True],
        "out.electricity.refrigerator.energy_consumption": ["refrigerator",float,True],
        "out.electricity.total.energy_consumption": ["total",float,True],
        "out.electricity.vehicle.energy_consumption": ["evcharger",float,True],
        "out.electricity.water_systems.energy_consumption": ["hotwater",float,True],
        "out.electricity.well_pump.energy_consumption": ["water",float,True],
        "out.fuel_oil.heating.energy_consumption": ["heating",float,False],
        "out.fuel_oil.total.energy_consumption": ["total",float,False],
        "out.fuel_oil.water_systems.energy_consumption": ["hotwater",float,False],
        "out.natural_gas.clothes_dryer.energy_consumption": ["dryer",float,False],
        "out.natural_gas.cooking_range.energy_consumption": ["cooking",float,False],
        "out.natural_gas.fireplace.energy_consumption": ["heating",float,False],
        "out.natural_gas.grill.energy_consumption": ["cooking",float,False],
        "out.natural_gas.heating.energy_consumption": ["heating",float,False],
        "out.natural_gas.hot_tub_heater.energy_consumption": ["heating",float,False],
        "out.natural_gas.lighting.energy_consumption": ["lights",float,False],
        "out.natural_gas.pool_heater.energy_consumption": ["heating",float,False],
        "out.natural_gas.total.energy_consumption": ["total",float,False],
        "out.natural_gas.water_systems.energy_consumption": ["hotwater",float,False],
        "out.propane.clothes_dryer.energy_consumption": ["dryer",float,False],
        "out.propane.cooking_range.energy_consumption": ["cooking",float,False],
        "out.propane.heating.energy_consumption": ["heating",float,False],
        "out.propane.total.energy_consumption": ["total",float,False],
        "out.propane.water_systems.energy_consumption": ["hotwater",float,False],
        "out.site_energy.total.energy_consumption": ["total",float,None],
        "out.wood.heating.energy_consumption": ["heating",float,False],
        "out.wood.total.energy_consumption": ["total",float,False],
    },
    "commercial" : {
        "county": None,
        "in.building_type": None,
        "models_used": None,
        "floor_area_represented": ["units",float,None],
        "out.district_cooling.cooling.energy_consumption": ["cooling",float,True],
        "out.district_heating.heating.energy_consumption": ["heating",float,True],
        "out.district_heating.water_systems.energy_consumption": ["hotwater",float,True],
        "out.electricity.cooling.energy_consumption": ["cooling",float,True],
        "out.electricity.exterior_lighting.energy_consumption": ["lights",float,True],
        "out.electricity.fans.energy_consumption": ["ventilation",float,True],
        "out.electricity.heat_recovery.energy_consumption": ["heating",float,True],
        "out.electricity.heat_rejection.energy_consumption": ["heating",float,True],
        "out.electricity.heating.energy_consumption": ["heating",float,True],
        "out.electricity.interior_equipment.energy_consumption": ["process",float,True],
        "out.electricity.interior_lighting.energy_consumption": ["lights",float,True],
        "out.electricity.pumps.energy_consumption": ["water",float,True],
        "out.electricity.refrigeration.energy_consumption": ["refrigerator",float,True],
        "out.electricity.water_systems.energy_consumption": ["hotwater",float,True],
        "out.natural_gas.heating.energy_consumption": ["heating",float,False],
        "out.natural_gas.interior_equipment.energy_consumption": ["process",float,False],
        "out.natural_gas.water_systems.energy_consumption": ["hotwater",float,False],
        "out.district_cooling.total.energy_consumption": ["cooling",float,False],
        "out.district_heating.total.energy_consumption": ["heating",float,False],
        "out.electricity.total.energy_consumption": ["total",float,True],
        "out.natural_gas.total.energy_consumption": ["total",float,False],
        "out.other_fuel.heating.energy_consumption": ["heating",float,False],
        "out.other_fuel.water_systems.energy_consumption": ["hotwater",float,False],
        "out.other_fuel.total.energy_consumption": ["total",float,False],
        "out.site_energy.total.energy_consumption": ["total",float,None],
    },
    "industrial" : {},
    "agricultural" : {},
    "transportation" : {},
}

ENDUSES = []
for sector in CONVERTERS:
    ENDUSES.extend([y[0] for x,y in CONVERTERS[sector].items() if isinstance(y,list) and y[2] != None])    
ENDUSES = list(set(ENDUSES)) + ["heatgain"]

TYPES = []
for types in BUILDING_TYPE.values():
    TYPES.extend(types.keys())

WEATHER = {"typical":"tmy3","actual":"amy2018"}
TIMEZONE = "UTC"
FLOATFORMAT = ".4g"

class EnduseError(Exception):
    """Enduse exception"""

class Enduse:
    """Enduse class"""
    def __init__(self,
            country:str,
            state:str,
            county:str|None,
            building_types:list[str]|None=None,
            weather:str='tmy3',
            timestep:str|None=None,
            electrification:dict={},
            ):
        """Access building enduse data

        Arguments:

        * `country`: country code (e.g., "US")

        * `state`: state abbreviation (e.g., "CA")

        * `county`: County name pattern (must by unique)

        * `building_type`: Building type regex (i.e., pattern matches start by
          default). See `BUILDING_TYPE` for valid building types

        * `timestep`: timeseries aggregate timestep (default '1h')

        * `electrification`: electrification fractions for enduses (see ENDUSES)
        """

        # prepare cache
        if country != "US":
            raise EnduseError("only US enduse data is available")
        self.country = country
        cachedir = os.path.join(os.environ["GLD_ETC"],".enduse",country,state,county,weather)
        os.makedirs(cachedir,exist_ok=True)

        # get location spec from Census Bureau
        self.state = state
        fips = census.Census(state,county)
        if fips.length() == 0:
            raise EnduseError(f"state='{state}' county='{county}' not found")
        if fips.length() > 1:
            raise EnduseError(f"state='{state}' county='{county}' not unique")
        fips = fips[fips.list()[0]]
        gcode = fips["gcode"]
        tzinfo = f"""{-int(re.match("[A-Z]+([+0-9]+)[A-Z]+",fips["tzspec"]).group(1)):+03.0f}:00"""
        self.county = county

        # get building enduse data from NREL
        if not isinstance(building_types,list) and not building_types is None:
            raise TypeError("building_types is not a list or None")
        if timestep == None:
            timestep = "1h"
        self.data = {}
        for pattern in '.*' if building_types is None else building_types:
            for sector,types in [(x,y) for x,y in BUILDING_TYPE.items()]:
                for btype,spec in [(x,y) for x,y in types.items() if re.match(pattern,x)]:

                    # handle cache
                    cachefile = os.path.join(cachedir,f"{btype.lower()}.csv.gz")
                    if os.path.exists(cachefile):
                        data = pd.read_csv(cachefile,index_col=[0],parse_dates=True)
                    else:
                        url = URL[sector].format(state=state,gcode=gcode,type=spec,weather=weather)
                        import urllib
                        try:
                            data = pd.read_csv(url,
                                usecols = list(range(2,len(CONVERTERS[sector])+1)),
                                index_col = [0],
                                parse_dates = True,
                                converters = {x:y[1] for x,y in CONVERTERS[sector].items() if isinstance(y,list)},
                                )
                            data.to_csv(cachefile,index=True,header=True)
                        except urllib.error.HTTPError as err:
                            app.error(f"{btype} not available ({err})")
                            continue

                    # resample timeseries
                    data = data.resample(timestep).sum()
                    data.index = data.index.tz_localize("EST").tz_convert(TIMEZONE if TIMEZONE else tzinfo)

                    # drop unused inputs
                    for field in [x for x in data.columns if x.startswith("in.")] \
                            + [x for x,y in CONVERTERS[sector].items() if y == None]:
                        if field in data.columns:
                            data.drop(field,axis=1,inplace=True)

                    # rename disaggregated fields
                    for field,convert in {x:y for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] == None}.items():
                        data.rename({field:convert[0]},inplace=True,axis=1)

                    # initialize aggregate fields
                    for field in ENDUSES:
                        data[field] = 0.0
                    electric_loads = {x:y[0] for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] == True}
                    for source,field in electric_loads.items():
                        data[field] += data[source]
                        data.drop(source,axis=1,inplace=True)

                    # check electrification
                    for field in electrification:
                        if field not in ENDUSES or field == "heatgain":
                            raise EnduseError(f"electrification '{field}' is not a valid enduse")

                    # compute heatgains and update fields
                    nonelectric_loads = {x:y[0] for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] == False}
                    for source,field in nonelectric_loads.items():
                        try:
                            factor = float(electrification[field])
                        except (KeyError, TypeError):
                            factor = 0.0
                        data["heatgain"] += data[source] * (1-factor)
                        data[field] += data[source] * factor
                        data.drop(source,axis=1,inplace=True)
                    for field in ENDUSES:
                        data[field] /= data["units"]
                    data.drop("units",axis=1,inplace=True)
                    self.data[btype] = data

    def has_buildingtype(self,building_type:str) -> bool:
        """Checks whether data include building type

        Argument:

        * `building_type`: building type to check

        Returns:

        * `bool`: building type found
        """
        return building_type in self.data

    def sum(self,building_type,enduse) -> bool:
        """Get total enduse energy for building_type

        Argument:

        * `building_type`: building type to check

        Returns:

        * `bool`: building type found
        """
        if not self.has_buildingtype(building_type):

            raise EnduseError(f"no enduse data found for building_type '{building_type}'")

        if not enduse in ENDUSES:

            raise EnduseError(f"no such enduse '{enduse}'")

        if not enduse in self.data[building_type].columns:

            raise EnduseError(f"building type '{building_type}' does not include enduse '{enduse}'")

        return self.data[building_type][enduse].sum()

    def to_player(self,
        csvname:str,
        building_type:str=".*",
        enduse:str=".*") -> dict:
        """Write player data

        Argument:

        * `csvname`: name of CSV file

        * `building_type`: regex pattern of building types (see TYPES)

        * `enduse`: regex pattern for enduses to write to CSV

        Returns:

        * `dict`: GLM objects needed to access players

        The `csvname` should include the `building_type` field, e.g., `mycsv_
        {building_type}` if more than one building type matches the
        `building_type` pattern.
        """
        glm = {}
        for bt,data in self.data.items():
            if not re.match(building_type,bt):
                continue
            eu = [x for x in data.columns if re.match(enduse,x)]
            if not csvname.endswith(".csv"):
                csvname += ".csv"
            if "{building_type}" not in csvname:
                file = "".join(os.path.splitext()(csvname).insert(1,f"_{bt.lower()}"))
            else:
                file = csvname.format(building_type=bt.lower())
            self.data[bt].to_csv(file,index=True,header=True,float_format=f"%{FLOATFORMAT}")
            glm[f"{self.country}_{self.state}_{self.county}_{bt.lower()}"] = {
                "class" : "tape.multiplayer",
                "file" : file,
            }
        return glm

    def to_glm(self,glmname:str,glmdata:dict):
        """Write GLM objects created by players"""
        properties = "\n    ".join([f"double {x}[kW];" for x in ENDUSES])
        with open(glmname,"w") as fh:
            print(f"""module tape;
class building 
{{
    {properties}
}}
""",file=fh)
            for name,data in glmdata.items():
                print(f"""object building
{{
    name "{name}";
    object {data['class']}
    {{
        file "{data['file']}";
    }};
}}
""",file=fh)



def main(argv:list[str]) -> int:
    """Enduse main routine

    Arguments:

    * `argv`: argument list (see Syntax for details)

    Returns:

    * `int`: exit code
    """
    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    location = {}
    electrification = {}
    output = None
    building_types = None
    weather = "tmy3"
    timestep = None
    output = None
    player = []
    model = None
    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        elif key in ["--local"]:

            TIMEZONE = ",".join(value)

        elif key in ["--type"]:

            if len(value) > 1:
                raise EnduseError("only one building type is allowed")
            if len(value) == 0 :
                raise EnduseError("a building type must be specified")
            building_type = value[0]

        elif key in ["--list"]:

            if len(value) > 1:
                raise EnduseError("only one feature is allowed")
            if len(value) == 0 :
                raise EnduseError("a feature must be specified")
            
            if "sector" in value:
            
                print("\n".join(SECTORS))
                return app.E_OK

            if "type" in value:

                for sector in SECTORS:
                    print("\n".join(list(BUILDING_TYPE[sector])))
                return app.E_OK

            if "country" in value:
            
                print("US")
                return app.E_OK

            if "state" in value:

                if not "country" in location or not location["country"] in ["US"]:
                    raise EnduseError("country not specified")
                print("\n".join(list(census.FIPS_STATES)))
                return app.E_OK

            if "county" in value:

                if not "country" in location or not location["country"] in ["US"]:
                    raise EnduseError("country not specified")
                if not "state" in location or not location["state"] in list(census.FIPS_STATES):
                    raise EnduseError("state not specified")
                raise NotImplementedError("unable to generate list of counties")

            if "enduse" in value:

                print("\n".join(ENDUSES))
                return E_OK

        elif key in ["--start"]:

            if len(value) > 1:
                raise EnduseError("only one start date is allowed")
            if len(value) == 0 :
                raise EnduseError("a start date must be specified")
            START = value

        elif key in ["--stop"]:

            if len(value) > 1:
                raise EnduseError("only one stop date is allowed")
            if len(value) == 0 :
                raise EnduseError("a stop date must be specified")
            STOP = value

        elif not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

        elif key in ["--player"]:

            player = value

        elif key in ["--model"] and len(value) > 0:

            if len(value) > 1:

                raise EnduseError("only one model glm file may be specified")

            model = value[0]
        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    enduse = Enduse(**location,
        building_types=[building_type],
        electrification=electrification,
        weather=weather,
        timestep=timestep,
        )

    glm = {}
    if player:

        for item in player:
            glm.update(enduse.to_player(item))

        if model:
            if model.endswith(".glm"):
                enduse.to_glm(model,glm)
    else:
        enduse.data[building_type].to_csv(open(output,"w") if output else sys.stdout)

    # normal termination condition
    return app.E_OK

def test():
    """Run self-test

    Returns:

    * `(int,int)`: number of failed test and number of tests performed
    """
    n_failed = n_tested = 0
    for btype in TYPES:
        n_tested += 1
        try:
            print("Testing",btype,end="...",flush=True)
            ls = Enduse("US","WA","Snohomish",[btype],electrification={"heating":1.0},weather="amy2018")
            if ls.has_buildingtype(btype):
                assert len(ls.data[btype]) == 8761, f"incorrect number of rows downloaded for building type {btype} (expected 8761, got {len(ls.data[btype])})"
                assert len(ls.data[btype].columns) == 20, f"incorrect number of columns downloaded for building type {btype} (expected 20, got {len(ls.data[btype].columns)})"
                for enduse in ENDUSES:
                    total = ls.sum(btype,enduse).round(1)
                    if total > 0:
                        print(enduse,"=",total,"kWh",end=", ",flush=True)
                print("ok")
        except:
            raise
            e_type,e_value,e_trace = sys.exc_info()
            print(f"FAILED: {__file__}@{e_trace.tb_lineno} ({e_type.__name__}) {e_value}")
            n_failed += 1

    return n_failed,n_tested

if __name__ == "__main__":

    if not sys.argv[0]:
    
        sys.argv = [__file__] + "US WA Snohomish --player=enduse_{building_type}.csv --model=test.glm --type=MOBILE".split()
        app.run(main)
        # app.test(test)

    else:

        app.run(main)

