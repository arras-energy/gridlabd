[[/GLM/Directive/Module]] -- GLM module load directive

# Synopsis

GLM:

~~~
module NAME;
~~~

# Description

The `module` load directive is used to load a GridLAB-D or Python modules into the solver framework.  Modules provide classes and event handlers.

If the module name is a Python module, it will be loaded in the core environment, which
automatically imports the `gldcore` module. See [[/Module/Python]] for details.

# See also

* [[/Module/Python]]
* [[/Developer/Module/Create]]
* [[/Developer/Class/Create]]
