[[/Module/Behavior]] -- Human behavior module

# Synopsis

GLM:

~~~
module behavior
{
	message_flags [DEBUG|QUIET|VERBOSE|WARNING];
	system_resolution 1e-9;
}
~~~

# Description

The `behavior` module implements various behavioral models that can be used to
modify properties of devices as a way of representing how individual
preferences and decisions affect devices.

## Continuous behavior

The `random` class is used to apply distributions directly to properties of
objects. See [[/Module/Behavior/Random]] for details.

## Discrete behavior

The `system` class is used to apply random states to properties of objects.
See [[/Module/Behavior/System]] for details.


# See also

* [[/Module/Behavior/Random]]
* [[/Module/Behavior/System]]
