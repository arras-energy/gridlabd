[[/GLM/Global/Random.md]] -- Generate a random number

# Synopsis

GLM:

~~~
${RANDOM}
${RANDOM SPEC}
~~~

# Description

If used without the `SPEC`, a random uniform number between 0 and 1 is
generated.

The following is permitted for `SPEC`:

* `N`: generate a `N`-bit unsigned integer where $0 \lt N \le 64$.

* `TYPE(A[,B])`: generate a random number of the specified distriction `TYPE`
  given the arguments provided. See [[/GLM/General/Random%20values.md]] for 
  a list of distributions and their arguments.

* `last`: return the last random number generated.

If no random number has been previously generated and `last` is called, the
value of the global `randomseed` is returned.

# Example

File `test.glm`:

~~~
#set suppress_repeat_messages=FALSE
#print Random uniform.......... ${RANDOM}
#print Random 8-bit integer... ${RANDOM 8}
#print Random 16-bit integer... ${RANDOM 16}
#print Random 32-bit integer... ${RANDOM 32}
#print Random 48-bit integer... ${RANDOM 48}
#print Random 64-bit integer... ${RANDOM 64}
#print Random normal........... ${RANDOM normal(0,1)}
#print Last number generated... ${RANDOM last}
~~~

Run the following:

~~~
gridlabd test.glm
~~~

Output:

~~~
./test.glm(2): Random uniform.......... 0.196869
./test.glm(3): Random 8-bit integer... 156
./test.glm(4): Random 16-bit integer... 238
./test.glm(5): Random 32-bit integer... 996881412
./test.glm(6): Random 48-bit integer... 5506770547858
./test.glm(7): Random 64-bit integer... 8577238717949152431
./test.glm(8): Random normal........... 1.33329
./test.glm(9): Last number generated... 1.33329
~~~

# See Also

* [[/GLM/General/Random%20values.md]]
