[[/Glm/Macro/Save]] -- Macro to save model in current state

# Synopsis

GLM:

~~~
#save "FILENAME.EXT"
~~~

# Description

The `#save` macro write the model to a file in its current state during the
load process.

# Examples

The following command save the model is JSON format.

~~~
#save ${modelname/.glm/.json}
~~~

# See also

* [[/GLM/Macro/Write]]
* [[/GLM/Macro/Input]]
