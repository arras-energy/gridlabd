"""NOAA Weather Archive Accessor

Syntax: gridlabd noaa_weather [OPTION ...] STATION 

Options:

    --list                          Get a list of available US stations
    -y|--year=[YEAR[-YEAR][,...]]   Specify years to download (default is current year)
"""
import os
import pandas as pd
import urllib
import gridlabd.framework as app
from gridlabd.nsrdb_weather import geohash
import datetime as dt

THISYEAR = dt.datetime.now().year
CACHEDIR = os.path.join(os.environ["GLD_ETC"],"noaa_weather")
os.makedirs(CACHEDIR,exist_ok=True)

class NOAAWeatherError:
    """NOAA Weather archive exception handler"""

class NOAAWeather:
    """NOAA Weather archive data"""

    SERVERURL = "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly"
    DATACOLUMNS = {
        "temperature": "temperature[degC]",
        "dew_point_temperature": "dewpoint[degC]",
        "station_level_pressure": "pressure[mbar]",
        "wind_direction": "winddir[deg]",
        "wind_speed": "windvel[knots]",
        "wind_gust": "windgusts[knots]",
        "precipitation": "rainfall[inch/h]",
        "relative_humidity": "humidity[%]",
        "visibility": "visibility[miles]",
        "pressure_3hr_change": "pressure_change[mbar/3h]",
        "sky_cover_1": "SKY1",
        "sky_cover_2": "SKY2",
        "sky_cover_3": "SKY3",
        }
    STATIONCOLUMNS = {
        "LATITUDE": "Y[deg]",
        "LONGITUDE": "X[deg]",
        "ELEVATION": "A[ft]",
        "STATE": "ST",
        "NAME": "NAME",
        "ICAO": "ICAO",
        }
    CLOUDS = {"CLR":0.0,"FEW":25.0,"SCT":50.0,"BKN":75.0,"OVC":100.0,"VV":99.0}

    @staticmethod
    def station_list(latlon=None,refresh=False):

        # download latest station list for airport codes
        pathname = os.path.join(CACHEDIR,".index")
        if not refresh and os.path.exists(pathname):
            data = pd.read_csv(pathname,index_col=[0])
        else:
            data = None
        if data is None:
            data = pd.read_csv(f"{NOAAWeather.SERVERURL}/doc/ghcnh-station-list.csv",
                index_col=["GHCN_ID"],
                usecols=["GHCN_ID"]+list(NOAAWeather.STATIONCOLUMNS),
                ).dropna(subset="ICAO").rename(NOAAWeather.STATIONCOLUMNS,axis=1)
            data.to_csv(pathname,index=True,header=True)
        if isinstance(latlon,(tuple,list)):
            dist = (data["X[deg]"]-latlon[1])**2 + (data["Y[deg]"]-latlon[0])**2
            ndx = dist.sort_values().index[0]
            return data.loc[[ndx]]
        else:
            return data

    def __init__(self,station,year=THISYEAR,refresh=None,fill=True,dropna=True):
        if refresh is None:
            refresh = year == THISYEAR
        pathname = os.path.join(CACHEDIR,f"{station}_{year}.csv")
        self.data = None
        if not refresh and os.path.exists(pathname):
            try:
                self.data = pd.read_csv(pathname,index_col=[0])
            except Exception as err:
                app.warning(f"'{pathname}' cache read error -- reloading from source")
        if self.data is None:
            try:
                url = f"{self.SERVERURL}/access/by-year/{year}/psv/GHCNh_{station}_{year}.psv"
                self.data = pd.read_csv(url,
                    usecols=["DATE"]+list(self.DATACOLUMNS),
                    index_col=["DATE"],sep="|",
                    parse_dates=["DATE"],
                    low_memory=False,
                    ).rename(self.DATACOLUMNS,axis=1)
                if fill:
                    self.data.ffill(inplace=True)
                    self.data.bfill(inplace=True)
                if dropna:
                    self.data.dropna(axis=1,inplace=True)
                # self.data["skycover[%]"] = [max(self.CLOUDS[x.split(":",2)[0]],self.CLOUDS[y.split(":",2)[0]],self.CLOUDS[z.split(":",2)[0]]) 
                #     for x,y,z in zip(self.data.SKY1.values,self.data.SKY2.values,self.data.SKY3.values)]
                self.data.drop(["SKY1","SKY2","SKY3"],axis=1,inplace=True)
                self.data.to_csv(pathname,index=True,header=True)
            except urllib.error.HTTPError as err:
                if app.DEBUG:
                    raise
                app.error(f"unable to download data for {station=} {year=} -- {err}")
                self.data = None

def main(argv:list[str]) -> int:

    # handle no options case -- typically a cry for help
    if len(argv) == 1:

        app.syntax(__doc__)
        return app.E_SYNTAX

    # handle stardard app arguments --debug, --warning, --verbose, --quiet, --silent
    args = app.read_stdargs(argv)
    station = None
    station_list = NOAAWeather.station_list()
    years = [THISYEAR]
    output = None

    for key,value in args:

        if key in ["-h","--help","help"]:
            
            print(__doc__,file=sys.stdout)
            return app.E_OK

        # add your options here
        if key in ["-l","--list"]:

            data = station_list.sort_index()
            data.dropna(subset="ST",axis=0,inplace=True)
            data.rename({
                    "Y[deg]": "latitude",
                    "X[deg]": "longitude",
                    "A[ft]": "altitude",
                    "ST": "state",
                    "NAME": "location",
                    "ICAO": "airport",
                    },
                axis=1,inplace=True)
            data["geocode"] = [geohash(x,y) for x,y in zip(data.latitude,data.longitude)]
            data.drop([x for x in data.index if not x.startswith("US")],axis=0,inplace=True)
            data.index.name="id"
            pd.options.display.width = None
            pd.options.display.max_columns = None
            pd.options.display.max_rows = None
            print(data.to_csv())
            return app.E_OK

        elif key in ["-y","--years"]:

            years = []
            for year in value:
                if "-" in year:
                    year = year.split("-",2)
                    years.extend(range(int(year[0]),int(year[1])+1))
                else:
                    years.append(year)

        elif key in station_list.index:

            station = key

        elif key in station_list.ICAO.values:

            station = station_list[station_list.ICAO==key].index.tolist()[0]

        elif key in ["-p","--position","--location"]:

            station = NOAAWeather.station_list([float(value[0]),float(value[1])]).index.tolist()[0]

        else:

            if value is None:
                app.error(f"'{key}' is invalid")
            else:
                app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    # implement your code here
    if station is None:
        error("no station specified",E_MISSING)

    # print(type(station),station)
    weather = pd.concat([NOAAWeather(station=station,year=int(x)).data for x in years],axis=0)

    if output is None:
        print(weather.to_csv(index=True,header=True))
    elif output.endswith(".csv"):
        weather.to_csv(output,index=True,header=True)
    else:
        app.error("invalid output file format",app.E_INVALID)

    # normal termination condition
    return app.E_OK

if __name__ == "__main__":

    app.run(main)
    
    # app.run(main,[__name__,"-l"])
    # app.run(main,[__name__,"KSFO","-y=2020"])
    # app.run(main,[__name__,"-p=37.5,-122.5"])

    # pd.options.display.width = None
    # pd.options.display.max_columns = None

    # app.DEBUG=True
    # location = NOAAWeather.station_list([37.5,-122.5])
    # location_name = str(location.index.tolist()[0])
    # print(NOAAWeather(location_name,2020,refresh=True).data)
