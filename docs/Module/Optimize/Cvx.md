[[/Module/Optimize/Cvx]] -- CVX optimizer

# Synopsis

~~~
module optimize
{
    cvx_backend CPP|SCIPY|NUMPY;
    cvx_failure_handling HALT|WARN|IGNORE;
    cvx_imports "SYMBOL[,...]";
    cvx_problemdump "FILENAME";
}
object cvx
{
    event {NONE,INIT,PRECOMMIT,PRESYNC,SYNC,POSTSYNC,COMMIT,FINALIZE};
    data "NAME:[OBJECT|CLASS|GROUP].PROPERTY[,...][;...]";
    variables "NAME=GLOBAL[&DUAL][;...]";
    variables "NAME=GROUP@PROPERTY[&DUAL][;...]";
    variables "NAME=CLASS:PROPERTY[&DUAL][;...]";
    variables "NAME=OBJECT.PROPERTY[&DUAL][;...]";
    objective "[Minimize|Maximize](EXPRESSION)";
    constraints "EXPRESSION[:OBJECT.PROPERTY][,...]";
    value DOUBLE;
    presolve "PYTHON_SCRIPT";
    postsolve "PYTHON_SCRIPT";
    solver_options "OPTION=VALUE[,...]";
}
~~~

# Description

The `cvx` object sets up a convex optimization using CVXPY.  The optimization
is run on any event included in the `event` set.  

Zero or more `data` references can be provided. References to objects are
singletons while references to groups and classes are vectors comprising all
members of the group or class. The `data` vector is assembled from the
specified values in the order which they are received. Classes and groups are
ordered by object id. The structure is always and $M \times N$ matrix where
$M$ is the number of objects (in rows) and $N$ is the number of properties
listed (in columns).  For example

    data "A=test.A1,...,test.AN;b=test.b"

will result in the following matrices

    A = [
        [test_1.A0, ... test_1.AN],
        ...
        [test_M.A0, ... test_M.AN]
    ]
    b = [
        [test_1.b],
        ...
        [test_M.b]
    ]

One or more `variables` may be specified in the same manner as `data`
definitions. If the dual is specified, it uses the same aggregation as the
primal property, e.g., `x=CLASS:PRIMAL&DUAL` will use `PRIMAL` as the primal
variable and `DUAL` as the dual variable in all object of `CLASS`. 

When the optimization is successful, the value of the objective function is
stored in the `value` and the values of all variables and duals are updated.

When the problem is infeasible or unbounded the variables are not updated and
the object properties are unchanged from the previous values. The only
indication that the problem is infeasible or unbounded is the property
`value` is `+inf` or `-inf`, respectively.

The `presolve` and `postsolve` scripts can be used to process additional Python code before and after the solver runs, respectively.  During the
`presolve` and `postsolve` scripts the following globals are defined in Python.

* `__cvx__`: a dictionary containing the problem `data`, `variables`, `objective`, `constraints`, `problem`, `result`, and `value`, for all the active problems in the GridLAB-D model. The keys to each problem are the name of the `cvx` objects which define the problem.

* `__dump__`: the file to which the problem dumps are written when the `cvx_problemdump` module global is specified.

# Caveat

1. It is often important to establish the correct rank for an optimizer so that
it runs after all the objects it depends on have updated their properties.
Use the `parent` property to ensure that the optimizer is initialized after
all the objects it depends on.

2. Each problem creates global data and variables before the problem is solved. If other problems have created variables by the same name, these are overwritten. However, this also means that a subsequent problem can access the results of a previously solved problem without going through the `__cvx__` global, provided the name isn't used by more than one problem. The order in which problem are evaluated can be controlled using the `cvx` object's parent property.

# Example

The following example illustrates how to run CVX using objects.

~~~
module optimize;
class test
{
    randomvar A0;
    randomvar A1;
    randomvar A2;
    randomvar A3;
    randomvar b;
    double x;
    double y;
    double mu;
}

object test:..3
{
    parent optimizer;
    name `test_{id}`;
    A0 "type:normal(0,1);refresh:1h";
    A1 "type:normal(0,1);refresh:1h";
    b "type:normal(0,1);refresh:1h";
}

object cvx 
{
    name "optimizer";
    event INIT;
    data "A=test.A0,test.A1,test.A2,test.A3";
    data "b=test.b";
    variables "x=test.x/mu,y:test.y";
    objective "Minimize(sum_squares(A@x-b))";
    constraints "0<=x";
    constraints "x<=1,y==2*x";
}
~~~

# See also 

* [https://cvxpy.org/]