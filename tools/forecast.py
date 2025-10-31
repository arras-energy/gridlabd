"""Forecast data access

Syntax: gridlabd forecast [OPTIONS ...] DATETIME[--DATETIME|+TIMEDELTA|][,...]

Options:

    -L|--location LAT/LON[,...]   Latitude/longitude of location(s)

    -G|--geocode GEOCODE[,...]    Geocode of location(s)

    -V|--variable NAME[,...]      Weather variable(s) to download

    --clean   Clean up data cache folder

    -o|--output FILENAME.EXT      File to save data in

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
import warnings
import shutil
import pandas as pd

warnings.simplefilter("error")

class ForecastError(Exception):

    def __init__(self,*args):

        Exception.__init__(self,args[0] if args else None)
        self.data = args[1:] if len(args) > 1 else None

GEOHASH_RESOLUTION=9
PRODUCTS = {
    "NOAA" : {
        "hrrr" : {
            "sfc": {
                "TMP:2 m above": {"name": "Temperature at 2 meters","attr":"t2m"},
                "DPT:2 m above": {"name": "Dewpoint at 2 meters","attr":"d2m"},
                "RH:2 m above": {"name": "Relative humidity at 2 meters","attr":"r2"},
                },
            # "prs": [],
            # "nat": [],
            # "subh": [],
            }, 
        },
    }
DATADIR = os.path.join(os.environ["GLD_ETC"],"herbie")

def guesstype(x):
    """Determine the basic type of a value"""

    # date/time value
    for dateformat in ["%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d %H","%Y-%m-%d"]:
        try:
            return dt.datetime.strptime(x,dateformat)
        except ValueError:
            pass

    # integer value
    try:
        return int(x)
    except:
        pass

    # real value
    try:
        return float(x)
    except:
        pass

    # complex value
    try:
        return complex(x)
    except:
        pass

    # string value
    try:
        return str(x)
    except:
        pass

    # cannot be reduce to a basic type
    return None

def to_point(x:str) -> tuple:
    """Convert string to a geocode tuple"""
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

def distance(a,b):
    """Get the distance between to geohashes"""
    return math.sqrt(distance2(a,b))

def distance2(a,b):
    """Get the distance squared between two geohashes"""
    x0,y0 = geocode(a)
    x1,y1 = geocode(b)
    dx,dy = x0-x1,y0-y1
    return dx*dx+dy*dy

def nearest(hash,hashlist):
    """Find the nearest geohash in a list of geohashes"""
    if len(hashlist) > 0:
        dist = sorted([(x,distance2(hash,x)) for x in hashlist],key=lambda y:y[1])
        return dist[0][0]
    else:
        return (None,float('nan')) if withdist else None

def data(*args,**kwargs):
    """Access Herbie forecast data

    Arguments:

    (see Herbie documentation at https://herbie.readthedocs.io/)

    Returns:

    Herbie xarray on success, None of failure

    Exceptions:

    ForecastError: Herbie data inventory error, i.e., no GRIB or no index
    """
    app.debug(f"entering data({','.join([repr(x) for x in args])},{','.join([f'{x}={repr(y)}' for x,y in kwargs.items()])})")
    kwargs["verbose"] = False # Herbie print statements contain non UTF-8 text that cannot be handled by some streams
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        H = Herbie(*args,save_dir=DATADIR,**kwargs)
        if not any([H.grib is not None, H.idx is not None]):
            raise ForecastError("unable to find data",app.E_FAILED)
        result = H.xarray
        app.debug(f"returning {result}")
        return result

def main(argv:list[str]) -> int:
    """Main routine"""

    # handle no options case -- typically a cry for help
    if len(argv) == 0:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)

    hargs = [] # current date/time
    hkwds = {} # model=hrrr/product=sfc/fxx=0
    points = {} # all locations (entire CONUS)
    variables = [] # 2m tmp, dpt, and rh
    output = [] # all to stdout

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
                    print("\n".join(f"""{n+1:3.0f}. {f'{m} -- {items[m]["name"]}' if isinstance(items,dict) else m}""" for n,m in enumerate(sorted(items))),flush=True)
                else:
                    app.error("subproduct listing not available",code=app.E_INVALID)
                    return app.E_INVALID
            return app.E_OK

        elif key in ["-L","--location"]:

            points = dict([to_point(",".join(x.split("/",2))) for x in value])

        elif key in ["-G","--geocode"]:

            points = dict([to_point(x) for x in value])
        
        elif key in ["-V","--variable"]:

            variables.extend(value)

        elif key in ["-o","--output"]:

            output.extend(value)

        elif key == "--clean":

            app.debug(f"cleaning {DATADIR}")
            if os.path.exists(DATADIR):
                shutil.rmtree(DATADIR)

        elif len(value) == 0:

            hargs.append(guesstype(key))

        elif key not in hkwds:

            hkwds[key] = guesstype(",".join(value))

        else:

            app.error(f"{key} already specified",code=app.E_INVALID)
            return app.E_INVALID
    try:

        if not hargs:
            hargs = [dt.datetime.now()]

        if not hkwds:
            hkwds = {"--model":"hrrr","--product":"sfc","--fxx":0}

        if not variables:
            variables = ["TMP:2 m above","DPT:2 m above","RH:2 m above"]

        if not output:
            output = ["-","-","-"] # send all variables to stdout

        try:
            xr = data(*hargs,**hkwds)
        except ForecastError as err:
            print(f"ERROR [forecast]: {err}")
            return err.exitcode
        except Exception as err:
            if app.DEBUG:
                raise
            print(f"ERROR [forecast]: {err}")
            return app.E_EXCEPTION

        # variables selected
        if variables:

            assert len(variables) == len(output), f"number of variables ({len(variables)}) does not match number of outputs ({len(output)})"
            for variable,ofile in zip(variables,output):
                attr = PRODUCTS["NOAA"][hkwds["--model"]][hkwds["--product"]][variable]["attr"]
                result = getattr(xr(variable),attr)

                # png image
                if ofile.endswith(".png"):

                    result.plot(cmap="Spectral_r", figsize=[8, 4]).figure.savefig(ofile)

                # text output to file
                elif ofile.endswith(".txt"):

                    with open(ofile,"w") as fh:
                        print(df,file=fh)

                elif points:
                    time = result.time.to_pandas()
                    values = result.to_pandas().stack()
                    latitude = result.latitude.to_pandas().stack()
                    longitude = result.longitude.to_pandas().stack()

                    geopanel = pd.concat({"temperature":values,
                        "latitude":latitude,
                        "longitude":longitude,
                        },axis=1)
                    geocodes = [geohash(x,(y-360 if y>180 else y),GEOHASH_RESOLUTION) for x,y in zip(latitude,longitude)]
                    geopanel["geocode"] = [geohash(x,(y-360 if y>180 else y),GEOHASH_RESOLUTION) for x,y in zip(latitude,longitude)]
                    geopanel["datetime"] = time
                    geopanel.set_index(["datetime","geocode"],inplace=True)
                    result = []
                    for point in points:
                        location = nearest(point,geocodes)
                        result.append(geopanel.loc[time,location])
                    df = pd.concat(result,axis=0)

                    # csv file
                    if ofile.endswith(".csv"):

                        df.to_csv(ofile,header=True,index=True)

                    # text output to stdout
                    elif ofile in ["-","stdout","/dev/stdout"]:

                        print(df,file=sys.stdout)

                    else:

                        raise ForecastError(f"'{ofile}' is not a supported output file type")
                else:

                    raise ForecastError(f"'{ofile}' is not a supported output file type")

        else:

            raise ForecastError(f"no variables specified")
    
    except Exception as err:
    
        app.exception(err)

    # implement your code here

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    # app.run(main,sys.argv[1:] if len(sys.argv) > 0 else [])

    # app.DEBUG = True
    # app.VERBOSE = True
    # app.run(main,[__name__,"-l"])
    # app.run(main,[__name__,"-l=NOAA"])
    # app.run(main,[__name__,"-l=NOAA/cfs"])
    # app.run(main,[__name__,"-l=NOAA/cfs/time_series"])
    # app.run(main,[__name__,"--model=cfs","--product=time_series","-p=37.5,-122.5"])
    # app.run(main,[__name__,"-l=NOAA/hrrr"])
    # app.run(main,[__name__,"-l=NOAA/hrrr/sfc"])
    # app.run(main,[__name__,"--model=hrrr","--product=sfc","-fxx=0","-v=TMP:2 m above"])
    # app.run(main,[__name__,"--model=hrrr","--product=sfc","--fxx=0","-v=TMP:2 m above","-p=37.5,-122.5"])
    # app.run(main,[__name__,"2025-10-25 09:00"])
    # app.run(main,[__name__,"clean"])
    app.run(main,[__name__,"--debug","2025-10-25 09:00","-G=9qd9xh,9x603v,9qd2ds"])
    # app.run(main,[__name__,"2025-10-25 10:00","-L=37.5/-122.5,48.5/-122.5"])
    # app.run(main,[__name__,"2025-10-25 10:00,2025-10-25 11:00,2025-10-25 12:00","-L=37.5/-122.5,48.5/-122.5"])
    # app.run(main,[__name__,"2025-10-25 00:00--2025-10-25 00:00","-L=37.5/-122.5,48.5/-122.5"])
    # app.run(main,[__name__,"2025-10-25 00:00+2D12H","-L=37.5/-122.5,48.5/-122.5"])
