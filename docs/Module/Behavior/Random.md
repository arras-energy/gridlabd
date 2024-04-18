[[/Module/Behavior/Random]] - Random continuous behavior

# Synopsis

~~~
module Behavior
{
	set {QUIET=65536, WARNING=131072, DEBUG=262144, VERBOSE=524288} message_flags; // module message control flags
	int32 retry_limit; // limit on the number of sampling retries when RETRY limits are in effect
}
class random 
{
	enumeration {RT_TRIANGLE=12, RT_BETA=11, RT_GAMMA=10, RT_WEIBULL=9, RAYLEIGH=8, EXPONENTIAL=6, PARETO=5, BERNOULLI=4, LOGNORMAL=3, NORMAL=2, UNIFORM=1, DEGENERATE=0} type; // Distribution type to be used to generate values
	double a; // The first distribution parameter value
	double b; // The second distribution parameter value
	double lower_limit; // The lower limit for generated values
	double upper_limit; // The upper limit for generated values
	enumeration {NONE=0, CLAMP=1, RETRY=2} limit_method; // Method to use to enforce limits
	double refresh_rate[s]; // The rate at which values are generated
	method point; // Point to which random value is posted as <object-name>:<property-name>
}
~~~

# Description

The `random` class is used to apply continuous distributions directly to double properties of objects. All the properties may be changes at any time. However validation is only performed during initialization.

The distribution type is specified by the `type` properties, with `a` and `b` providing the arguments to the distribution.  The `lower_limit` and `upper_limit` values are used to perform clipping. There are three kind of limits.

* `NONE`: the limits are not imposed on the samples.

* `CLAMP`: the limits are imposed by clamping the output to the specified range. The result does not change the probabilities within the limits, but increases the probability of sampling the limits themselves.

* `RETRY`: the limits are imposed by resampling when a sample is outside the specified range. The result does not change the shape of the probability density function within the limits, but increases the probability of observing values within the limits.

The `refresh_rate` property determines how often the target values are updated.

The `point` method allows one or more target values to be added. Points are specified as `<object-name>.<property-name>`.  Generally point are specified at initialization, but in some cases they can be added during the simulation. However, points cannot be removed once they are added.

# Caveat

Using `limit_method RETRY` can affect performance when the limits constrain the range to a relatively unlikely part of the distribution. In such cases, the `retry_limit` may be easily exceeded in a non-deterministic manner.

# Example

~~~
module Behavior;
class test
{
	double x;
	double y;
}
object test
{
	name human_1;
}
object behavior.random
{
	type NORMAL;
	a 0;
	b 1;
	refresh_rate 1h;
	lower_limit -1;
	upper_limit +1;
	limit_method RETRY;
	point "human_1.x";
}
~~~

# See also

* [[/Module/Behavior]]
