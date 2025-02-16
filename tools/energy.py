"""Access energy use load shape data from NREL"""

import collections

SECTORS = ["commercial","residential","industrial","agricultural","transportation"]
URL = collections.namedtuple("URL",SECTORS)(
    "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/comstock_tmy3_release_1/timeseries_aggregates/by_county/state%3D{state}/g{fips}-{type}.csv",
    "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_tmy3_release_1/timeseries_aggregates/by_county/state%3D{state}/g{fips}-{type}.csv",
    None,
    None,
    None,
    )
BUILDING_TYPE = collections.namedtuple("BUILDING_TYPE",SECTORS)(
    {
        "MOBILE":"mobile_home",
        "MULTI_FAMILY_SMALL" : "multi-family_with_2_-_4_units",
        "MULTI_FAMILY_LARGE" : "multi-family_with_5plus_units",
        "SINGLE_FAMILY_ATTACHED" : "single-family_attached",
        "SINGLE_FAMILY_DETACHED" : "single-family_detached",
        },
    {
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
    None,
    None,
    None,
    )

class Energy:

    def __init__(self,country,state,county,building_type=None):

        self.state = state
        self.data = collections.namedtuple("ENERGY_DATA",SECTORS)(*[{}]*len(SECTORS))

if __name__ == "__main__":

    ls = Energy("US","CA","San Mateo",["MOBILE"])
    print(ls.data)