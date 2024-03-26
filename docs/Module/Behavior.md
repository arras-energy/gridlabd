[[/Module/Behavior]] -- Human behavior module

# Synopsis

GLM:

~~~
module behavior
{
	message_flags [DEBUG|QUIET|VERBOSE|WARNING];
}
~~~

# Description

The `behavior` module implements various behavioral models that can be used to
modify properties of devices as a way of representing how individual
preferences and decisions affect devices.

## Continuous `random` behavior

The `random` class is used to apply distributions directly to properties of
objects. See [[/Module/Behavior/Random]] for details.

## Discrete `exclusive` behavior

The `exclusive` class is used to apply discrete choice distributions directly
to `enumeration` properties of objects. See [[/Module/Behavior/Exclusive]] to
details.

## Discrete `inclusive` behavior

The `inclusive` class is used to apply discrete choice distributions directly
to `set` properties of objects. See [[/Module/Behavior/Inclusive]] to details.

# See also

* [[/Module/Behavior/Exclusive]]
* [[/Module/Behavior/Inclusive]]
* [[/Module/Behavior/Random]]
