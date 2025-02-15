"""Buildings

Syntax: gridlabd buildings [OPTIONS ...]

Options:

* `-C|--county=COUNTRY/STATE/COUNTY`: download county-level data

* `-L|--locate`: include latitude and longitude

* `-A|--address: include address (warning: this can take a long time to process)

* `-o|--output=FILENAME`: output to a file

* `--nocache`: do not use cache data

* `--cleancache`: clean cache data
"""

import os
import sys
import pandas as pd
import requests
import urllib
import gridlabd.framework as app
from gridlabd.resource import Resource
import gridlabd.geodata_address as address
from gridlabd.nsrdb_weather import geocode
from typing import TypeVar

class BuildingsError(app.ApplicationError):
    """Buildings exception"""

class Buildings:
    """Buildings data"""
    def __init__(self,country:str,state:str,county:str,locate:bool=False,address:bool=False,cache:[bool|str]=True) -> TypeVar('pd.DataFrame'):
        """Construct buildings object

        Arguments:

        * `country`: specifies the country

        * `state`: specify the state, province, or region)

        * `county`: specify the county

        * `locate`: enable addition of latitude and longitude data

        * `address`: enable addition of address data (can be very slow)

        * `cache`: control cache (use 'clean' to refresh cache data)
        """
        pathname = os.path.join(os.environ["GLD_ETC"],".buildings",country,f"{state}_{county}.csv.gz")
        filedir,filename = os.path.split(pathname)

        # check cache option
        if cache not in [False,True,"clean"]:
            raise BuildingsError(f"invalid cache value (cache={repr(cache)})")
        
        # clean cache
        if cache == "clean" and os.path.exists(pathname):
            os.remove(pathname)

        # use cache
        if cache and os.path.exists(pathname):

            self.data = pd.read_csv(pathname)
            changed = False

        # read from source
        else:
            self.data = Resource().content(name="buildings",index=f"{country}/{filename}")
            changed = True

        # handle latlon include option
        if locate and ("latitude" not in self.data.columns or "longitude" not in self.data.columns):

            self._add_latlon()
            changed = True

        # handle address include option
        if address and "address" not in self.data.columns:

            self._add_address()
            changed = True

        # save cache
        if cache and changed:

            self.data.to_csv(pathname,index=False,header=True)

    def _add_latlon(self):

        latlon = [geocode(x) for x in self.data["centroid"].tolist()]
        self.data["latitude"] = [x[0] for x in latlon]
        self.data["longitude"] = [x[1] for x in latlon]

    def _add_address(self):

        self.data["address"] = address.apply(self.data)

def main(argv:list[str]) -> int:

    OUTPUT = None
    LOCATE = False
    ADDRESS = False
    CACHE = True

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    country,state,county = [None]*3

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        elif key in ["-A","--address"]:

            ADDRESS = True

        elif key in ["-C","--county"] and len(value[0].split("/")) == 3:

            country,state,county = value[0].split("/")

        elif key in ["-L","--locate"]:

            LOCATE = True

        elif key in ["-o","--output"]:

            OUTPUT = value

        elif key == "--nocache":

            CACHE = False

        elif key == "--cleancache":

            CACHE = "clean"
        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    if country is None or state is None or county is None:

        raise BuildingsError("country, state, county not specified")

    result = Buildings(country,state,county,LOCATE,ADDRESS,CACHE)
    result.data.to_csv(open(OUTPUT,"w") if OUTPUT else sys.stdout)

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    app.run(main)