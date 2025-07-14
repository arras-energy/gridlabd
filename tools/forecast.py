"""Forecast data access

Syntax: gridlabd forecast [OPTIONS ...] COMMAND [ARGUMENTS ...]

Options:

Commands:

The `forecast` tool provides access to recent and archived numerical weather
prediction model outputs from different cloud archive sources delivered by
Herbie. 

See also:
* https://github.com/blaylockbk/Herbie
"""

import os
import sys
import datetime as dt
import gridlabd.framework as app
from gridlabd.nsrdb_weather import geocode,geohash
from herbie import Herbie
from herbie.models.cfs import time_series_variables as cfs_time_series

GEOHASH_RESOLUTION=9
PRODUCTS = {
    "NOAA" : {
        "cfs" : {
            "time_series": cfs_time_series,
            },
        # "gefs" : {},
        # "gfs" : {},
        # "hafsa" : {},
        # "hiresw" : {},
        # "href" : {},
        "hrrr" : {
            "sfc": {
                "TMP:2 m above": "Temperature at 2 meters",
                "DPT:2 m above": "Dewpoint at 2 meters",
                "RH:2 m above": "Relative humidity at 2 meters",
                },
            "prs": [],
            "nat": [],
            "subh": [],
            }, 
        # "hrrrak" : {},
        # "nam" : {},
        # "nbm" : {},
        # "rap" : {},
        # "rrfs" : {},
        # "rtma" : {}, 
        # "rtma_ak" : {},
        # "urma" : {}, 
        # "utma_ak" : {},
        },
    # "ECMWF": {
    #     "ecmwf" : {},
    #     "azure" : {},
    #     "aws" : {},
    #     },
    # "ECCC" : {
    #     "gdps" : {},
    #     "hrdps" : {},
    #     "rdps" : {},
    #     },
    # "USNAVY": {
    #     "navgem_nomads" : {},
    #     "nogaps_ncei" : {},
    #     },
}

DATE = dt.datetime.now()

def guesstype(x):

    for dateformat in ["%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d %H","%Y-%m-%d"]:
        try:
            return dt.datetime.strptime(x,dateformat)
        except ValueError:
            pass

    try:
        return int(x)
    except:
        pass

    try:
        return float(x)
    except:
        pass

    try:
        return complex(x)
    except:
        pass

    return str(x)

def to_point(x):
    if "," in x:
        xy = [float(x) for x in x.split(",")]
        try:
            return (geohash(*xy,GEOHASH_RESOLUTION),tuple(xy))
        except:
            return (x,None)
    else:
        try:
            return (x,geocode(x))
        except:
            return (x,None)

def main(argv:list[str]) -> int:

    # handle no options case -- typically a cry for help
    if len(argv) == 0:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    hargs = []
    hkwds = {}
    points = {}
    variable = None

    for key,value in args:

        if key in ["-h","--help","help"]:
            
            print(__doc__,file=sys.stdout)
            return app.E_OK

        # add your options 
        if key in ["-l","--list"]:

            for source in value if value else PRODUCTS.keys():
                spec = source.split("/") if value else []
                if len(spec) == 0:
                    print(source)
                elif len(spec) == 1:
                    if not spec[0] in PRODUCTS:
                        app.error(f"{spec[0]} is not a valid forecast model source",code=app.E_NOTFOUND)
                    print(f"{source}:")
                    items = PRODUCTS[spec[0]]
                    print("\n".join(f"{n+1:3.0f}. {m}" for n,m in enumerate(sorted(items))),flush=True)
                elif len(spec) == 2:
                    if spec[1] not in PRODUCTS[spec[0]]:
                        app.error(f"{spec[1]} is not found in {spec[0]}",code=app.E_NOTFOUND)
                    print(f"{'/'.join(value)}:")
                    items = PRODUCTS[spec[0]][spec[1]]
                    print("\n".join(f"{n+1:3.0f}. {m}" for n,m in enumerate(sorted(items))),flush=True)
                elif len(spec) == 3:
                    if spec[2] not in PRODUCTS[spec[0]][spec[1]]:
                        app.error(f"{spec[2]} is not found in {spec[0]/spec[1]}",code=app.E_NOTFOUND)
                    print(f"{'/'.join(value)}:")
                    items = PRODUCTS[spec[0]][spec[1]][spec[2]]
                    print("\n".join(f"{n+1:3.0f}. {f'{m} ({items[m]})' if isinstance(items,dict) else m}" for n,m in enumerate(sorted(items))),flush=True)
                else:
                    app.error("subproduct listing not available",code=app.E_INVALID)
                    return app.E_INVALID
            return app.E_OK

        elif key in ["-p","--position","--points"]:

            points = dict([to_point(x) for x in ",".join(value).split(";")])
        
        elif key in ["-v","--variable"]:

            variables = value

        elif len(value) == 0:

            hargs.append(guesstype(key))

        elif key not in hkwds:

            hkwds[key] = guesstype(",".join(value))

        else:

            app.error(f"{key} already specified",code=app.E_INVALID)
            return app.E_INVALID
    try:

        if not hargs:
            hargs = [DATE]
        app.verbose(f"calling Herbie({','.join([repr(x) for x in hargs])},{','.join([f'{x}={repr(y)}' for x,y in hkwds.items()])})...",file=sys.stderr)
        H = Herbie(*hargs,verbose=False,**hkwds)
        if any([H.grib is not None, H.idx is not None]):
            xr = H.xarray()
            if points:
                print(points)
            elif variable:
                print(xr[variable])
            else:
                print(xr)
            return app.E_OK
        else:
            app.error("unable to find data",code=app.E_FAILED)
            return app.E_FAILED
    
    except Exception as err:
    
        app.exception(err)

    # implement your code here

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    # app.DEBUG = True
    # app.VERBOSE = True
    app.run(main,[__name__,"-l"])
    app.run(main,[__name__,"-l=NOAA"])
    app.run(main,[__name__,"-l=NOAA/cfs"])
    app.run(main,[__name__,"-l=NOAA/cfs/time_series"])
    app.run(main,[__name__,"-l=NOAA/hrrr"])
    app.run(main,[__name__,"-l=NOAA/hrrr/sfc"])
    app.run(main,[__name__,"--model=hrrr","--product=sfc","--fxx=0","-v=TMP:2 m above","-p=37.5,-122.5;IL"])
