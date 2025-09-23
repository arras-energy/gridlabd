[[/Module/Powerflow/Zipload]] -- Class zipload

# Synopsis

GLM:

~~~
  object zipload {
    parent load;
    weather "<object>";
    Theat <decimal> degF;
    Tcool <decimal> degF;
    Zp_H "<decimal> W/degF";
    Zp_C "<decimal> W/degF";
    Zp_S "<decimal> W*h/Btu";
    Zp_W "<decimal> W/mph";
    Zp_R "<decimal> W*h/in";
    Zp "<decimal> W";
    Zq_H "<decimal> W/degF";
    Zq_C "<decimal> W/degF";
    Zq_S "<decimal> W*h/Btu";
    Zq_W "<decimal> W/mph";
    Zq_R "<decimal> W*h/in";
    Zq "<decimal> W";
    Ip_H "<decimal> W/degF";
    Ip_C "<decimal> W/degF";
    Ip_S "<decimal> W*h/Btu";
    Ip_W "<decimal> W/mph";
    Ip_R "<decimal> W*h/in";
    Ip "<decimal> W";
    Iq_H "<decimal> W/degF";
    Iq_C "<decimal> W/degF";
    Iq_S "<decimal> W*h/Btu";
    Iq_W "<decimal> W/mph";
    Iq_R "<decimal> W*h/in";
    Iq "<decimal> W";
    Pp_H "<decimal> W/degF";
    Pp_C "<decimal> W/degF";
    Pp_S "<decimal> W*h/Btu";
    Pp_W "<decimal> W/mph";
    Pp_R "<decimal> W*h/in";
    Pp "<decimal> W";
    Pq_H "<decimal> VAr/degF";
    Pq_C "<decimal> VAr/degF";
    Pq_S "<decimal> VAr*h/Btu";
    Pq_W "<decimal> VAr/mph";
    Pq_R "<decimal> VAr*h/in";
    Pq "<decimal> VAr";
    H "<decimal> degF";
    C "<decimal> degF";
    S "<decimal> Btu/h";
    W "<decimal> mph";
    R "<decimal> in/h";
    Z "<string> Ohm";
    I "<string> A";
    P "<string> VA";
    load_class "{RESIDENTIAL,COMMERCIAL,INDUSTRIAL,AGRICULTURAL,TRANSPORATION,PUBLICSERVICE}";
    load_type "<string>";
    schedule "<string>";
  }
~~~

# Description

A `zipload` object describes a load with constant impedance (`Z`), current
(`I`), and power (`P`) all given in Watts, with sensitivities to weather,
i.e., temperature, humidity, solar gains, wind, and rainfall. In addition,
the loads and their sensitivities can be scaled according to a schedule
varying by month of year, day of week, and hour of day.

If `load_class` and `load_type` are specified, then the load parameters are
obtained from the load data file specified by the module global
`zipload_data`. The default file is `ziploads.csv` and is stored in the 
`${GLD_ETC}` folder.

The `weather` is used to update the temperature (`T`), humidity (`H`), solar
gains (`S`), wind (`W`), and rainfall (`R`) values to drive the sensitivity
functions.

The load composition for impedance, current, and power are specified at the
nominal voltage of the bus to which the load is connected and updated as a
function of the voltage of the bus.

## Properties

### `weather`

TODO

### `Theat`

TODO

### `Zp_C`

TODO

### `Zp_C`

TODO

### `Zp_S`

TODO

### `Zp_W`

TODO

### `Zp_R`

TODO

### `Zp`

TODO

### `Zq_H`

TODO

### `Zq_C`

TODO

### `Zq_S`

TODO

### `Zq_W`

TODO

### `Zq_R`

TODO

### `Zq`

TODO

### `Im_H`

TODO

### `Im_C`

TODO

### `Im_S`

TODO

### `Im_W`

TODO

### `Im_R`

TODO

### `Im`

TODO

### `Ia_H`

TODO

### `Ia_C`

TODO

### `Ia_S`

TODO

### `Ia_W`

TODO

### `Ia_R`

TODO

### `Ia`

TODO

### `Pp_H`

TODO

### `Pp_C`

TODO

### `Pp_S`

TODO

### `Pp_W`

TODO

### `Pp_R`

TODO

### `Pp`

TODO

### `Pq_H`

TODO

### `Pq_C`

TODO

### `Pq_S`

TODO

### `Pq_W`

TODO

### `Pq_R`

TODO

### `Pq`

TODO

### `input_temp`

TODO

### `input_humid`

TODO

### `input_solar`

TODO

### `input_wind`

TODO

### `input_rain`

TODO

### `output_imped_p`

TODO

### `output_imped_q`

TODO

### `output_current_m`

TODO

### `output_current_a`

TODO

### `output_power_p`

TODO

### `output_power_q`

TODO

### `output_impedance`

TODO

### `output_current`

TODO

### `output_power`

TODO

### `load_class`

Flag to track load type, not currently used for anything except sorting

# Caveat

It is not advised to use constant power loads for a significant fraction of the
loads in a model as this can result is solver convergence problems.

# See also

* [[/Module/Powerflow]]
* [[/Module/Powerflow/Triplex_zipload]]

