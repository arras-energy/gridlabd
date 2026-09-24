"""Beginner's Guide to GridLAB-D GLM Files

GridLAB-D is an open-source power distribution simulation tool developed by
Pacific Northwest National Laboratory (PNNL). Models are written as plain
text files with a `.glm` extension — short for "GridLAB Model." This guide
walks through the basic structure of a GLM file and how to write your first
one.

What a GLM File Is
------------------

A GLM file describes a simulation using four main building blocks:

1. **Clock** – defines the simulation's start and stop time.

2. **Modules** – load the physics/behavior engines you need (e.g., power flow,
climate, residential loads).

3. **Configurations** – reusable specs like line conductors, transformer
settings, or line spacing.

4. **Objects** – the actual components of your model (nodes, lines, loads,
meters, recorders, etc.).

GLM syntax is C-like: statements end in semicolons, blocks are wrapped in
curly braces, and `//` starts a comment.

Setting Up the Clock
--------------------

Every simulation needs a `clock` block that sets the timezone and the
start/stop times:

```c
clock
{
     timezone "EST+5EDT";
     starttime "2024-01-01 00:00:00";
     stoptime "2024-01-02 00:00:00";
}
```

Loading Modules
---------------

Modules give GridLAB-D its capabilities. For a basic distribution model you'll
typically need at least the `powerflow` module:

```c
module powerflow
{
     solver_method NR;   // Newton-Raphson solver
}

module tape;   // enables players and recorders for input/output
```

Other common modules include `climate`, `residential`, `commercial`, `market`,
and `reliability`, depending on what you're modeling.

Defining Configurations
-----------------------

Before you can create lines and transformers, you often need to define their
electrical properties as configuration objects. For example, a simple
overhead line configuration:

```c
object line_configuration
{
     name "lc_conf_1";
     conductor_A "obj_conductor";
     conductor_B "obj_conductor";
     conductor_C "obj_conductor";
     conductor_N "obj_conductor";
     spacing "obj_line_spacing";
}
```

Configurations are usually defined once and referenced by multiple line or
transformer objects, which keeps your file organized and avoids repetition.

Creating Objects
----------------

Objects are the heart of a GLM file. Every object has a `class` (e.g., `node`,
`overhead_line`, `transformer`, `load`) and a set of properties. The general
syntax is:

```c
object CLASS
{
     name "NAME";
     property_1 value_1;
     property_2 value_2;
     ...
}
```

**Example: A node**

```c
object node
{
     name "node_1";
     phases ABCN;
     nominal_voltage 7200;
}
```

**Example: A line connecting two nodes**

```c
object overhead_line
{
     name "line_1";
     phases ABCN;
     from node_1;
     to node_2;
     length 500;
     configuration lc_conf_1;
}
```

**Example: A load**

```c
object load
{
     name "load_1";
     parent "node_2";
     phases ABCN;
     nominal_voltage 7200;
     constant_power_A 50000+20000j;
     constant_power_B 50000+20000j;
     constant_power_C 50000+20000j;
}
```

Note the `from`/`to` fields on the line — GridLAB-D builds its network
topology by connecting objects through references like these, along with
`parent` for objects that attach to (and inherit voltage from) another
object.

Getting Data In and Out
-----------------------

- **Players** feed time-series data (like a CSV) into an object property over
    the simulation:

```c
object player
{
     parent "load_1";
     property "constant_power_A";
     file "load_data.csv";
}
```

- **Recorders** capture a property's value over time and write it to a file:

```c
object recorder
{
     parent "node_2";
     property "voltage_A";
     file "voltage_output.csv";
     interval 60;
}
```

Putting It All Together
-----------------------

A minimal complete GLM file looks like this:

```c
clock
{
     timezone "EST+5EDT";
     starttime "2024-01-01 00:00:00";
     stoptime "2024-01-01 01:00:00";
}

module powerflow
{
     solver_method NR;
}
module tape;

object node
{
     name "node_1";
     phases ABCN;
     bustype SWING;
     nominal_voltage 7200;
}

object node
{
     name "node_2";
     phases ABCN;
     nominal_voltage 7200;
}

object overhead_line_conductor
{
     name "olc_1";
     geometric_mean_radius 0.0244;
     resistance 0.306;
}

object line_spacing
{
     name "ls_1";
     distance_AB 2.5;
     distance_BC 2.5;
     distance_AC 4.5;
     distance_AN 5.0;
     distance_BN 5.0;
     distance_CN 5.0;
}

object line_configuration
{
     name "lc_1";
     conductor_A olc_1;
     conductor_B olc_1;
     conductor_C olc_1;
     conductor_N olc_1;
     spacing "ls_1";
}

object overhead_line
{
     name "line_1";
     phases ABCN;
     from "node_1";
     to "node_2";
     length 500;
     configuration "lc_1";
}

object load
{
     name "load_1";
     parent "node_2";
     phases ABCN;
     nominal_voltage 7200;
     constant_power_A 50000+20000j;
     constant_power_B 50000+20000j;
     constant_power_C 50000+20000j;
}

object recorder
{
     parent "node_2";
     property "voltage_A";
     file voltage_output.csv;
     interval 60;
}
```

Save this as `model.glm` and run it from the command line:

```
gridlabd model.glm
```

If everything is set up correctly, GridLAB-D will run the simulation and write
`voltage_output.csv` with the recorded voltage at `node_2` over time.

Tips for Beginners
------------------

- **Indentation isn't required** but keep it consistent. GLM files get long
    fast, and readability matters.

- **Names must be unique** across the whole model. Reference other objects by
    name (as in `from`, `to`, `parent`, `configuration`).

- **Complex numbers** for power and impedance use the `<real>+<imaginary>i` or
    `<real>+<imaginary>j` format (e.g., `50000+20000j`), but
    `<magnitude>+<angle>d` or `<magnitude>+<angle>r` for voltages and
    currents.

- **Include units** for real and complex values to ensure that units are
    consistent with internal module units and conversion are performed
    automatically as needed.

- **A SWING bus is required** — this is your reference/slack bus, usually
    where the substation or source connects (set with `bustype SWING`).

- **Comment liberally** with `//` because people like comments.

- **Use `#include`** to split large models into multiple files, e.g.
    
         #include "configurations.glm"
         #include "network.glm"
         #include "generators.glm"
         #include "loads.glm"
         #include "players.glm"
         #include "recorders.glm"

- **Validate incrementally** by building up your model in small pieces (a couple
    of nodes and a line first) and run it often rather than writing hundreds
    of lines before testing.

Where to Go Next
----------------

- The online [GridLAB-D documentation](https://docs.gridlabd.us/) covers the
  full object/class reference for each module.

- The [taxonomy feeder models](https://github.com/arras-energy/gridlabd-models/) are a great way to study realistic, full-scale
  GLM files once you're comfortable with the basics.

- Explore modules like `residential` (houses, HVAC, appliances) and `climate`
  (weather-driven simulations) once you're comfortable with the core
  `powerflow` objects used in the taxonomy feeder models.
"""

import os
import sys
import json
import shutil
import tempfile
import warnings

from glm_command import glm_command

__all__ = ["GLMCompileException","GLM"] # specify what pdoc will publish

class GLMCompileException(Exception):
     """General GLM exception handler

     Attributes
     ----------
     - `exitcode`: the exit code (integer)
     - `output`: a list of output lines
     - `errors`: a list of error messages
     """
     def __init__(self,msg,exitcode,output,errors):

          self.output = exitcode
          """A list of output lines from the GLM compiler"""
          
          self.errors = output
          """A list of output errors from the GLM compiler"""
          
          self.exitcode = errors
          """The compiler exit code as an integer (0 is success, non-zero is failed)"""
          
          super().__init__(msg)

class GLM:
     """Basic GLM compiler

     Attributes
     ----------
     - `application`: always `"gridlabd"`
     - `version`: gridlabd version
     - `globals`: list of globals defined in the model
     - `classes`: list of classes defined in the model
     - `filter`: filter objects (optional)
     - `header`: header property definitions
     - `modules`: modules loaded in the model
     - `objects`: objects defined in the model
     - `schedules`: schedules defined in the model (optional)
     - `types`: data types used by the model
     """
     def __init__(self,
          glmfile:str,
          on_error:str='exception',
          define:dict[str,str]=None):
          """Compile a GLM file

          Arguments
          ---------
          - `glmfile`: the GLM file name to compile
          - `on_error`: error handling
            - `"ignore"`: the error is ignored and `exitcode` is set
            - `"warning"`: a warning is output and `exitcod` is set
            - `"exception"`: a GLMCompileException exception is raised (default)
          - `define`: global variable definitions
          """
          self.output = None
          """A list of output lines from the GLM compiler"""
          
          self.errors = None
          """A list of output errors from the GLM compiler"""
          
          self.exitcode = None
          """The compiler exit code as an integer (0 is success, non-zero is failed)"""

          assert on_error in ["ignore","exception","warning"]
          assert glmfile.endswith(".glm"), f"{glmfile=} must have a '.glm' extension"
          try:
               with tempfile.TemporaryDirectory() as tmp:
                    jsonfile = os.path.join(tmp,os.path.basename(glmfile.replace(".glm",".json")))
                    args = ["-C",glmfile,"-o",jsonfile]
                    for key,value in (define if define else {}).items():
                         args = ["-D",f"{key}={value}"] + args
                    result = glm_command(*args)
                    
                    self.output = result.stdout.split("\n")
                    self.errors = result.stderr.split("\n")
                    self.exitcode = result.returncode
                    if self.exitcode == 0:
                         with open(jsonfile,"r") as fh:
                              data = json.load(fh)
                              assert data["application"] == "gridlabd", f"{glmfile} is not a GridLAB-D GLM file"
                              for key,value in [(x,y) for x,y in data.items() if x not in ["application"]]:
                                   setattr(self,key,value)
                    elif on_error != "ignore":
                         msg = f"{glmfile=} compile failed (exitcode {self.exitcode}), see `output` and `errors` for details"
                         if on_error == "exception":
                              raise GLMCompileException(msg,self.exitcode,self.output,self.errors)
                         warnings.warn(msg)
          except:
               raise
          finally:
               shutil.rmtree(tmp,ignore_errors=True)

# Included for dev testing purposes only -- do not uncomment for releases
if __name__ == '__main__':

     # this should work
     glm = GLM("autotest/test_assert.glm",define={"verbose":"TRUE"})
     assert len(glm.objects) > 0, "no object loaded"
     assert glm.errors[-2] == "   ... exit code 0"

     # this should fail with an exception
     try:
          glm = GLM("autotest/test_assert1.glm")
     except GLMCompileException:
          pass

     # this should fail with a warning
     with warnings.catch_warnings(record=True) as wf:
          glm = GLM("autotest/test_assert1.glm",on_error="warning")

          # verify the warning
          assert str(wf[0].message) == "glmfile='autotest/test_assert1.glm' compile failed (exitcode 5), see `output` and `errors` for details"

     # this should fail with an exception
     try:
          glm = GLM("autotest/test_assert1.glm",on_error="exception")
     except GLMCompileException:
          pass
