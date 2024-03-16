[[/Module/Pypower/Powerplant]] -- PyPower powerplant object

# Synopsis

~~~
class powerplant {
    char32 city; // City in which powerplant is located
    char32 state; // State in which powerplant is located
    char32 zipcode; // Zipcode in which powerplant is located
    char32 country; // Country in which powerplant is located
    char32 naics_code; // Powerplant NAICS code
    char256 naics_description; // Powerplant NAICS description
    int16 plant_code; // Generator plant code number
    set {CC=1024, PV=512, CT=256, ES=128, WT=64, FW=32, IC=16, AT=8, ST=4, HT=2, UNKNOWN=1} generator; // Generator type
    set {NG=32768, COAL=16384, WATER=8192, NUC=4096, GAS=2048, OTHER=1024, WOOD=512, UNKNOWN=256, OIL=128, BIO=64, WASTE=32, COKE=16, GEO=8, SUN=4, WIND=2, ELEC=1} fuel; // Generator fuel type
    enumeration {ONLINE=1, OFFLINE=0} status; // Generator status
    double operating_capacity[MW]; // Generator normal operating capacity (MW)
    double summer_capacity[MW]; // Generator summer operating capacity (MW)
    double winter_capacity[MW]; // Generator winter operating capacity (MW)
    double capacity_factor[pu]; // Generator capacity factor (pu)
    char256 substation_1; // Substation 1 id
    char256 substation_2; // Substation 2 id
    complex S[VA]; // power generation (VA)
    char256 controller; // controller python function name
}
~~~

# Description

TODO

# Example

TODO

# See Also

* [[Module/Pypower]]
* [[Module/Pypower/Controllers]]
