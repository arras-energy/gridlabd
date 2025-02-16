"""Access energy use load shape data from NREL"""

import sys
import re
import json
import gridlabd.eia_recs as eia
import pandas as pd
try:
    import census
    print("WARNING: using local copy of census",file=sys.stderr)
except:
    import gridlabd.census as census

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
    "residential": "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_tmy3_release_1/timeseries_aggregates/by_county/state%3D{state}/{gcode}-{type}.csv",
    "commercial": "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/comstock_tmy3_release_1/timeseries_aggregates/by_county/state%3D{state}/{gcode}-{type}.csv",
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
class EnergyError(Exception):
    pass

class Energy:

    def __init__(self,country,state,county,building_types=None,timestep=None,electrification=None):
        """Access building energy use data

        Arguments:

        * `country`: country code (e.g., "US")

        * `state`: state abbreviation (e.g., "CA")

        * `county`: County name pattern (must by unique)

        * `building_type`: Building type regex (i.e., pattern matches start by
          default). See `BUILDING_TYPE` for valid building types
        """
        if country != "US":
            raise EnergyError("only US energy data is available")

        # get location spec from Census Bureau
        self.state = state
        fips = census.Census(state,county)
        if fips.length() == 0:
            raise EnergyError(f"state='{state}' county='{county}' not found")
        if fips.length() > 1:
            raise EnergyError(f"state='{state}' county='{county}' not unique")
        gcode = fips[fips.list()[0]]["gcode"]

        # get building energy data from NREL
        if not isinstance(building_types,list) and not building_types is None:
            raise TypeError("building_types is not a list or None")
        if timestep == None:
            timestep = "1h"
        self.data = {}
        for pattern in '.*' if building_types is None else building_types:
            for sector,types in [(x,y) for x,y in BUILDING_TYPE.items()]:
                for btype,spec in [(x,y) for x,y in types.items() if re.match(pattern,x)]:
                    url = URL[sector].format(state=state,gcode=gcode,type=spec)
                    data = pd.read_csv(url,
                        usecols = list(range(2,len(CONVERTERS[sector])+1)),
                        index_col = [0],
                        parse_dates = True,
                        converters = {x:y[1] for x,y in CONVERTERS[sector].items() if isinstance(y,list)},
                        ).resample(timestep).sum()
                    for field in [x for x in data.columns if x.startswith("in.")] \
                            + [x for x,y in CONVERTERS[sector].items() if y == None]:
                        data.drop(field,axis=1,inplace=True)
                    for field,convert in {x:y for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] == None}.items():
                        data.rename({field:convert[0]},inplace=True,axis=1)
                    aggregates = []
                    for field in list(set([y[0] for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] != None])):
                        data[field] = 0.0
                        aggregates.append(field)
                    electric_loads = {x:y[0] for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] == True}
                    for source,field in electric_loads.items():
                        data[field] += data[source]
                        data.drop(source,axis=1,inplace=True)
                    data["heatgain"] = 0.0
                    aggregates.append("heatgain")
                    nonelectric_loads = {x:y[0] for x,y in CONVERTERS[sector].items() if x in data.columns and isinstance(y,list) and y[2] == False}
                    for source,field in nonelectric_loads.items():
                        if electrification is None or field not in electrification:
                            data["heatgain"] += data[source]
                        else:
                            data[field] += data[source]
                        data.drop(source,axis=1,inplace=True)
                    for field in aggregates:
                        data[field] /= data["units"]
                    self.data[btype] = data


if __name__ == "__main__":

    ls = Energy("US","WA","Snohomish",["MOBILE"])
    # json.dump(dict(zip(list(ls.data["MOBILE"].columns),[None]*len(ls.data["MOBILE"].columns))),fp=sys.stdout,indent=4)
    pd.options.display.max_columns = None
    pd.options.display.max_rows = None
    pd.options.display.width = None
    print(ls.data["MOBILE"])
