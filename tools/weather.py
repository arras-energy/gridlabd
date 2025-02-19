"""Access weather data from NREL

Syntax: gridlabd weather COUNTRY STATE COUNTY TYPE [OPTIONS ...]

Options:

Description:

The `weather` tool downloads weather data from the NREL building stock data
respositories. This weather data is used for building energy modeling, but
can also be used for other purposes in GridLAB-D.

The only COUNTRY supported now is `US`.  The 


Example:

"""

import os
import sys
import re
import json
import gridlabd.eia_recs as eia
import pandas as pd
import gridlabd.census as census
import gridlabd.framework as app
import gridlabd.timeseries as ts

WEATHER_URL = {
    "tmy3": "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_tmy3_release_1/weather/tmy3/{gcode}_tmy3.csv",
    "amy2018" : "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/weather/amy2018/{gcode}_2018.csv"
    }

WEATHER_COLUMNS = {
    "Dry Bulb Temperature [°C]": "drybulb[degC]",
    "Relative Humidity [%]": "humidity[%]",
    "Wind Speed [m/s]": "wind_speed[m/s]",
    "Wind Direction [Deg]": "wind_dir[deg]",
    "Global Horizontal Radiation [W/m2]" : "solar_horizontal[W/m^2]",
    "Direct Normal Radiation [W/m2]": "solar_direct[W/m^2]",
    "Diffuse Horizontal Radiation [W/m2]": "solar_diffuse[W/m^2]",
}

TIMEZONE = "UTC"

FLOATFORMAT = ".1g"

START = None
END = None

TIMESTEP = "1h"

class WeatherError(Exception):
    """Weather exception"""

class Weather:
    """Weather class"""
    def __init__(self,
            country:str,
            state:str,
            county:str|None,
            weather_type:str='tmy3',
            timestep:str|None=None,
            ignore_errors:bool=False
            ):
        """Access weather data

        Arguments:

        * `country`: country code (e.g., "US")

        * `state`: state abbreviation (e.g., "CA")

        * `county`: County name pattern (must by unique)

        * `weather_type`: Specify type of weather data to download. Valid
          values are `tmy3` and `amy2018`.

        * `timestep`: timeseries aggregate timestep (default '1h')

        * `ignore_errors`: ignore download errors
        """

        # prepare cache
        if country != "US":
            raise WeatherError("only US enduse data is available")
        self.country = country
        cachedir = os.path.join(os.environ["GLD_ETC"],".weather")
        os.makedirs(cachedir,exist_ok=True)

        # get location spec from Census Bureau
        self.state = state
        fips = census.Census(state,county)
        if fips.length() == 0:
            raise WeatherError(f"state='{state}' county='{county}' not found")
        if fips.length() > 1:
            raise WeatherError(f"state='{state}' county='{county}' not unique")
        fips = fips[fips.list()[0]]
        gcode = fips["gcode"]
        tzinfo = f"""{-int(re.match("[A-Z]+([+0-9]+)[A-Z]+",fips["tzspec"]).group(1)):+03.0f}:00"""
        self.county = county

        # get building enduse data from NREL
        if timestep is None:
            timestep = TIMESTEP
        if not weather_type in WEATHER_URL:
            raise TypeError(f"weather_type {weather_type} is valid")
        self.data = {}

        # handle weather cache
        cachefile = os.path.join(cachedir,f"{country}_{state}_{county}_{weather_type}.csv.gz")
        if os.path.exists(cachefile):
            data = pd.read_csv(cachefile,index_col=[0],parse_dates=True)
        else:
            url = WEATHER_URL[weather_type].format(gcode=gcode.upper())
            print("Downloading",url,"...")
            import urllib
            try:
                data = pd.read_csv(url,
                    index_col = [0],
                    parse_dates = True,
                    dtype = float,
                    )
                data.to_csv(cachefile,index=True,header=True)
            except urllib.error.HTTPError as err:
                app.error(f"weather not available ({err} for {url})")
                if ignore:
                    return
                raise
        data.columns = [WEATHER_COLUMNS[x] for x in data.columns]
        data.index = pd.date_range("2018-01-01 00:00:00","2019-01-01 00:00:00",freq="1h")[:-1]

        # resample weather data
        data = data.resample(timestep).sum()
        data.index = data.index.tz_localize("EST").tz_convert(TIMEZONE if TIMEZONE else tzinfo)

        # save results
        self.data = data

    def to_player(self,
        csvname:str,
        ) -> dict:
        """Write player data

        Argument:

        * `csvname`: name of CSV file

        Returns:

        * `dict`: GLM objects needed to access players
        """
        if START or END:
            if not ( START and END ):
                raise WeatherError("both start and end dates must be specified")

        glm = {}
        for bt,data in self.data.items():
            if not re.match(building_type,bt):
                continue
            eu = [x for x in data.columns if re.match(enduse,x)]
            if not csvname.endswith(".csv"):
                csvname += ".csv"
            if START and END:
                timestep = f"{(self.data[bt].index[1] - self.data[bt].index[0]).total_seconds()/60}min"
                daterange = pd.DatetimeIndex(pd.date_range(start=START,end=END,freq=timestep))
                ndx = ts.project_daterange(self.data[bt].index,target=daterange,align='week')
                result = self.data[bt].loc[ndx.values()]
                result.index = list(ndx)
                result.index.name = "timestamp"
            else:
                result = self.data[bt]
            result.to_csv(csvname,index=True,header=True,float_format=f"%{FLOATFORMAT}")
            glm[f"{self.country}_{self.state}_{self.county}_weather"] = {
                "class" : "tape.multiplayer",
                "file" : csvname,
            }
        return glm

    def to_glm(self,glmname:str,glmdata:dict):
        """Write GLM objects created by players"""
        properties = "\n    ".join([f"double {x};" for x in sorted(WEATHER_COLUMNS.values())])
        with open(glmname,"w") as fh:
            print(f"""module tape;
module climate;
class weather 
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
    """Weather main routine

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
    output = None
    weather = "tmy3"
    timestep = None
    player = None
    model = None
    for key,value in args:

        if key in ["-h","--help","help"] and len(value) == 0:
            print(__doc__,file=sys.stdout)

        elif key in ["--local"] and len(value) == 0:

            TIMEZONE = ",".join(value)

        elif key in ["--start"] and 0 < len(value) < 2:

            global START
            START = value[0]

        elif key in ["--end"] and 0 < len(value) < 2:

            global END
            END = value[0]

        elif key in ["--player"]:

            player = value[0]

        elif key in ["--model"] and 0 < len(value) > 2:

            model = value[0]

        elif key in ["--type"] and 0 < len(value) < 2 and value[0] not in WEATHER_URL:

            weather = value[0]

        elif not key.startswith("-"):

            tag = ["country","state","county"][len(location)]
            location[tag] = key

        else:

            app.error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    weather = Weather(**location,
        weather_type=weather,
        timestep=timestep,
        )

    glm = {}

    if player:

        if player.endswith(".csv"):

            glm.update(enduse.to_player(player))

        else:

            raise WeatherError("unable to output player to non CSV format")

    else:

        weather.data.to_csv(open(output,"w") if output else sys.stdout)

    if model:

        if model.endswith(".glm"):
            weather.to_glm(model,glm)
        else:
            raise WeatherError("unable to output model in non GLM format")

    # normal termination condition
    return app.E_OK

def test():
    """Run self-test

    Returns:

    * `(int,int)`: number of failed test and number of tests performed
    """
    n_failed = n_tested = 0
    for wtype in WEATHER_URL:
        n_tested += 1
        try:
            print("Testing",wtype,end="...",flush=True)
            df = Weather("US","WA","Snohomish",weather_type=wtype,ignore_errors=True)
            assert len(df.data) == 8760, f"incorrect number of weather rows downloaded ({len(df.data)} found)"
            assert len(df.data.columns) == 7, f"incorrect number of weather columns downloaded ({len(df.data)} found)"
            avg,std = df.data.mean().round(1),df.data.std().round(1)
            print(", ".join([f"{x.split('[')[0]} = {avg[x]}+/-{std[x]} {x.split('[')[1][:-1]}" for x in df.data.columns]),end="... ok\n",flush=True)
        except:
            e_type,e_value,e_trace = sys.exc_info()
            print(f"FAILED: {__file__}@{e_trace.tb_lineno} ({e_type.__name__}) {e_value}")
            n_failed += 1

    return n_failed,n_tested

if __name__ == "__main__":

    if not sys.argv[0]:
    
        # dev test
        # sys.argv = [__file__,"US","WA","Snohomish","--start=2020-12-01 00:00:00-08:00","--end=2021-02-01 00:00:00-08:00"] 
        # app.run(main)
        # quit()

        app.read_stdargs([__file__])
        app.test(test)

    else:

        app.run(main)

