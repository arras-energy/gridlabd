[[/Converters/Import/Pypower_cases]] -- PyPower case input

# Synopsis

GLM:

~~~
#input "casefile.py" -t pypower [-N|--name]
~~~

Shell:

~~~
$ gridlabd convert -i inputfile.py -o outputfile.glm -t pypower [-N|--name]
~~~

# Description

The `py2glm.py` converter support conversion of PyPower case files to GLM
models.  The `-N|--name` option suppresses autonaming of PyPower objects.

# See also

* [[/Module/Pypower]]
