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

GEOHASH_RESOLUTION=9
MODELS = {
    "NOAA" : {
        "cfs" : {"time_series","6_hourly","monthly_means"},
        "gefs" : {},
        "gfs" : {},
        "hafsa" : {},
        "hiresw" : {},
        "href" : {},
        "hrrr" : {}, 
        "hrrrak" : {},
        "nam" : {},
        "nbm" : {},
        "rap" : {},
        "rrfs" : {},
        "rtma" : {}, 
        "rtma_ak" : {},
        "urma" : {}, 
        "utma_ak" : {},
        },
    "ECMWF": {
        "ecmwf" : {},
        "azure" : {},
        "aws" : {},
        },
    "ECCC" : {
        "gdps" : {},
        "hrdps" : {},
        "rdps" : {},
        },
    "USNAVY": {
        "navgem_nomads" : {},
        "nogaps_ncei" : {},
        },
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

    for key,value in args:

        if key in ["-h","--help","help"]:
            
            print(__doc__,file=sys.stdout)
            return app.E_OK

        # add your options 
        if key in ["-l","--list"]:

            for source in value if value else MODELS.keys():
                spec = source.split("/") if value else []
                if len(spec) == 0:
                    print(source)
                elif len(spec) == 1:
                    if not spec[0] in MODELS:
                        app.error(f"{spec[0]} is not a valid forecast model source",app.E_NOTFOUND)
                    print(f"{source}:")
                    print("\n".join(f"{n+1:3.0f}. {m}" for n,m in enumerate(sorted(MODELS[spec[0]]))))
                elif len(spec) == 2:
                    if spec[1] not in MODELS[spec[0]]:
                        app.error(f"{spec[1]} is not found in {spec[0]}")
                    print(f"{'/'.join(value)}:")
                    print("\n".join(f"{n+1:3.0f}. {m}" for n,m in enumerate(sorted(MODELS[spec[0]][spec[1]]))))
                else:
                    app.error("subproduct listing not available",app.E_INVALID)
                    return app.E_INVALID
            return app.E_OK

        elif key in ["-p","--position","--points"]:

            points = dict([to_point(x) for x in ",".join(value).split(";")])
        
        elif len(value) == 0:

            hargs.append(guesstype(key))

        elif key not in hkwds:

            hkwds[key] = guesstype(",".join(value))

        else:

            app.error(f"{key} already specified",app.E_INVALID)
            return app.E_INVALID
    try:

        if not hargs:
            hargs = [DATE]
        print(f"calling Herbie({','.join([repr(x) for x in hargs])},{','.join([f'{x}={repr(y)}' for x,y in hkwds.items()])})...",file=sys.stderr)
        H = Herbie(*hargs,verbose=False,**hkwds)
        if any([H.grib is not None, H.idx is not None]):
            xr = H.xarray()
            if not points:
                print(xr)
                return app.E_OK
            print(points)
        else:
            app.error("unable to find data",app.E_FAILED)
            return app.E_FAILED
    
    except Exception as err:
    
        app.exception(err)

    # implement your code here

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    # app.DEBUG = True
    app.run(main,[__name__,"-p=37.5,-122.5;IL"])
