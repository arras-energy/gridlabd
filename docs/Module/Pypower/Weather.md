[[/Module/Pypower/Weather]] -- PyPower weather object

# Synopsis

~~~
class weather {
	char1024 file; // Source object for weather data
	char1024 variables; // Weather variable column names (col1,col2,...)
	double resolution[s]; // Weather time downsampling resolution (s)
	double Sn[W/m^2]; // Solar direct normal irradiance (W/m^2)
	double Sh[W/m^2]; // Solar horizontal irradiance (W/m^2)
	double Sg[W/m^2]; // Solar global irradiance (W/m^2)
	double Wd[deg]; // Wind direction (deg)
	double Ws[m/2]; // Wind speed (m/2)
	double Td[degC]; // Dry-bulb air temperature (degC)
	double Tw[degC]; // Wet-bulb air temperature (degC)
	double RH[%]; // Relative humidity (%)
	double PW[in]; // Precipitable_water (in)
	double HI[degF]; // Heat index (degF)
}
~~~

# Description

The `weather` object reads data from a weather CSV file. The columns
in the CSV file are mapped according to the `variables` property.

The `bus` object includes the `weather` file properties, which allows
individual busses to read weather data directly.

# Example

The following example reads weather data in bus 1 of the IEEE 14 bus model.

~~~
module pypower
{
	solver_method NR;
}
#input "case14.py" -t pypower
modify pp_bus_1.weather_file ${DIR:-.}/case14_bus1_weather.csv;
modify pp_bus_1.weather_variables Sh,Sn,Sg,Wd,Ws,Td,Tw,RH,PW;
~~~

# See also

- [[/Module/Pypower]]
