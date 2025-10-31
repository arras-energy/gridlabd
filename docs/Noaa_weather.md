[[/Tools/Noaa_weather]] -- NOAA Weather Archive Accessor

Syntax: gridlabd noaa_weather [OPTION ...] STATION 

Options:

    --list                          Get a list of available US stations

    -o|--output=FILENAME.csv        Specify the output file name (default to stdout)

    -y|--year=[YEAR[-YEAR][,...]]   Specify years to download (default is current year)

    -p|--position=LAT,LON           Specify latitude longitude to search for nearest station

Description:

The `noaa_weather` tools downloads one or more years of weather data from NOAA's weather archive. Weather stations can be specified using the NOAA GNCH
ID code or the airport code.  The `-p=LAT,LON` option can be used to find the
nearest station to the specified position.

Data source:

The data source is https://www.ncei.noaa.gov/oa/global-historical-climatology-network/.

Climate data:

The following data climate data fields are provided

- temperature (degC)
- dewpoint (degC)
- pressure (mbar)
- winddir (deg)
- windvel (knots)
- windgusts (knots)
- rainfall (inch/h)
- humidity (%)
- visibility (miles)
- pressure_change (mbar/3h)
- skycover (%)

Station data:

The following data is provided for stations

- latitude (deg)
- longitude (deg)
- state
- city
- airport
- geocode

Sky cover data: 

Sky cover codes are converted as follows:

- `CLR` --> 0%
- `FEW` --> 25%
- `SCT` --> 50%
- `BKN` --> 75%
- `VV` --> 99%
- `OVC` --> 100%

Of the three sky-cover fields delivered by NOAA, the maximum sky-coverage found is used for the sky-cover percentage.
