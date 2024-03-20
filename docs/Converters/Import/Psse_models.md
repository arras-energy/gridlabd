[[/Converters/Import/Psse_model]] -- PSS/E model converter

# Synopsis

GLM:

~~~
#input "MODEL.raw"
~~~

Shell:

~~~
$ gridlabd MODELNAME.raw [-D pypower::OPTION=VALUE [...]]
~~~

# Description

The PSS/E `raw` model converter generates a `glm` file the can be solved by
the `pypower` module.

# Caveats

Only `bus`, `branch`, `gen`, and `transformer` objects are generated. All
other data records are converter to runtime classes with the prefix `psse_`.
In particular, switched shunts are not converted into functional objects.
A warning is generated for any PSS/E data encountered which cannot be 
converted to GLM objects.

# See also

* [[/Module/Pypower]]
* [[/Converters/Import/Pypower_cases]]
