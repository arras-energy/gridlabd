[[/Module/Python/Property]] -- Direct property access python objects

# Synopsis

Python:

~~~
import gldcore
gldcore.property.__init__(object=<int>, property=<str>)
gldcore.property.__init__(object=<str>, property=<str>)
gldcore.property.__eq__(<gldcore.property>)
gldcore.property.__ne__(<gldcore.property>)
gldcore.property.convert_unit(<str>)
gldcore.property.get_initial()
gldcore.property.get_name()
gldcore.property.get_unit()
gldcore.property.get_value()
gldcore.property.rlock()
gldcore.property.set_name(<str>)
gldcore.property.set_object(<int>)
gldcore.property.set_object(<str>)
gldcore.property.set_value(<str>)
gldcore.property.set_value(<long>)
gldcore.property.set_value(<float>)
gldcore.property.set_value(<complex>)
gldcore.property.set_value(<object>)
gldcore.property.unlock()
gldcore.property.wlock()
~~~

# Description

The `property` object provides direct high-performance access to GridLAB-D object properties.  Access is provided through strong-typed accessors that are tied to the GridLAB-D property types.

Objects can be identified by number (int) or name (str).  Properties may only be identified by name (str).

Values can be provided either as a string or a value that is compatible with the internal property in GridLAB-D.  When the value is provided as a string, it is parsed in the same manner as a GLM value.

Values can be retrieved only as the python type associated with the GridLAB-D property type.  To retrieve the value as a string, you must use the `str()` method.  In this case, the value is converted using GridLAB-D's output conversion methods for the property type.

# Example

The following example illustrates access to various object property types.

`example.glm`:

~~~
module example;
#set savefile=gldcore.json
clock
{
	starttime "2000-01-01 00:00:00";
	stoptime "2000-02-01 00:00:00";
}
class example_class
{
	python my_list;
	complex my_value;
	char32 my_string;
	double my_real[m/s];
}
object example_class
{
	name "my_example";
	my_list list(['test',12.34,dict(a=123,b=456)]);
	my_value 1.234+5.6789j;
	my_string "this is a short string";
	my_real 100 ft/s;
}
~~~

`example.py`:

~~~
import gldcore
def on_init(t):
	for name in ['my_list','my_value','my_string','my_real']:
		prop = gldcore.property('my_example',name)
		print(f"{repr(prop)}={str(prop)}")
	return True
~~~

`output`:

~~~
<gldcore.property:my_example.my_list>=['test', 12.34, {'a': 123, 'b': 456}]
<gldcore.property:my_example.my_value>=+1.234+5.6789j
<gldcore.property:my_example.my_string>="this is a short string"
<gldcore.property:my_example.my_real>=+30.48 m/s
~~~
