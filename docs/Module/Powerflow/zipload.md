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

A `zipload` object describes a 3-phase load with constant impedance (`Z`), current
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

# Caveat

It is not advised to use constant power loads for a significant fraction of the
loads in a model as this can result is solver convergence problems.

# See also

* [[/Module/Powerflow]]
* [[/Module/Powerflow/Triplex_zipload]]

