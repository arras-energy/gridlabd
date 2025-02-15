[[/Tools/Buildings]] -- Buildings

Syntax: gridlabd buildings [OPTIONS ...]

Options:

* `-C|--county=COUNTRY/STATE/COUNTY`: download county-level data

* `-L|--locate`: include latitude and longitude

* `-A|--address: include address (warning: this can take a long time to process)

* `-o|--output=FILENAME`: output to a file

* `--nocache`: do not use cache data

* `--cleancache`: clean cache data

Description:

The `buildings` module accessing the building model database used to generate building
objects in GridLAB-D.

Examples:

To download buildings data from the command line
~~~
gridlabd buildings -C=US/NH/Sullivan
~~~

To access building data in Python

~~~
gridlabd python
>>> import gridlabd.buildings
>>> gridlabd.buildings.Buildings("US","NH","Sullivan").data
                              id climate  year   centroid                                       footprint  height  ground_area  code  class  mixed  type  0      87M95X2C+XC65-13-14-14-13      6A     0  drsv2zwhg               drsv2zwhe18,bcz,j756,jjb2,ucx,uk3     5.4        119.8     5      1  False     0   
1      87M95X3C+7H47-15-14-15-14      6A     0  drsv2zy3j                      drsv2zy2vbx,34x1,3skb,3pwq     6.6        145.8     7      3  False     0   
2        87M95XQQ+C4QJ-11-9-11-9      6A     0  drsv9q4rg                       drsv9q4r7qb,ct2,6255f,sv7     3.8         69.0     1      1  False     0   
3      87M95XQQ+95GJ-15-18-16-17      6A     0  drsv9q4qv  drsv9q4wb8j,qmyh,que2,qer5,r433,rm5k,qyw1,rp9u     5.3        170.4     2      3  False     0   
4      87M95XPJ+Q24Q-12-10-12-11      6A     0  drsv9juty                       drsv9jutx11,u3q,wjz2,vbr5     5.1         95.0     5      1  False     0   
...                          ...     ...   ...        ...                                             ...     ...          ...   ...    ...    ...   ...   
27571  87M96HQF+7RQ9-12-16-13-17      6A  1890  drsmzzm2y                      drsmzzm353c,90vq,893d,27tv    10.5        228.0     1      1  False    91   
27572  87M99M94+8C96-33-32-36-30      6A  1965  drsw9yby8  drsw9ybznxv,yjt4,y60g,v924,tew2,ws6h,wtk0,xw0v     7.0        914.1     1     11  False   150   
27573    87M99M97+VXMQ-16-8-15-8      6A  1910  drsw9zpny                       drsw9zppm6h,reg,q80x,nmyz     7.2        123.0     1      1  False     7   
27574   87M9CWVQ+MX5X-10-10-10-9      6A     0  drsz0hz88                       drsz0hz80y6,2qtc,2z9v,9fr     5.0         72.1     1      1  False     0   
27575   87M99J6X+PM69-10-17-9-18      6A  1983  drsw9tg8x               drsw9tg87z4,guj,v7e,vrk,bfn4,b3vq     3.0        194.6     2      1  False    91   

       windows  floors  floor_area  
0        0.140       1       119.8  
1        0.300       2       291.7  
2        0.140       1        69.0  
3        0.300       1       170.4  
4        0.140       1        95.0  
...        ...     ...         ...  
27571    0.140       3       684.1  
27572    0.006       1       914.1  
27573    0.140       2       245.9  
27574    0.140       1        72.1  
27575    0.140       1       194.6  

[27576 rows x 14 columns]
~~~



# Classes

## Buildings

Buildings data

### `Buildings(country:str, state:str, county:str, locate:bool, address:bool, cache:[bool | str])`

Construct buildings object

Arguments:

* `country`: specifies the country

* `state`: specify the state, province, or region)

* `county`: specify the county

* `locate`: enable addition of latitude and longitude data

* `address`: enable addition of address data (can be very slow)

* `cache`: control cache (use 'clean' to refresh cache data)


---

## BuildingsError

Buildings exception

# Functions

## `main() -> int`

Main routine

Arguments:

* `argv`: command line argument list (see module docs for details)

Returns:

* `int`: exit code

