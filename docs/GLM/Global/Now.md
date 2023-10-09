[[/GLM/Global/Now.md]] -- Get current time

# Synopsis

GLM:

~~~
${NOW}
${NOW FORMAT}
~~~

# Description

If used without the `FORMAT`, then the format used is `%Y%m%d-%H%M%S`.

# Example

File `/tmp/test.glm`:

~~~
#print ${NOW}
#print ${NOW %m/%d/%y %H:%M}
~~~

Run the following:

~~~
gridlabd /tmp/test.glm
~~~

Output:

~~~
20231008-101445
10/08/23 10:14
~~~
