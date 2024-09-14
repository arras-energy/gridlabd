[[/Module/Optimize/Cvx]] -- CVX optimizer

# Synopsis

~~~
module optimize
{
    cvx_backend CPP|SCIPY|NUMPY;
    cvx_options VERBOSE|GP|QCP|GRADIENTS;
    cvx_dpp DEFAULT|ENFORCE|IGNORE;
    cvx_solver CBC|CLARABEL|COPT|DAQP|GLOP|GLPK|GLPK_MI|OSQP|PIQP|PROXQP|PDLP|CPLEX|NAG|ECOS|GUROBI|MOSEK|CVXOPT|DSPA|SCS|SCIP|XPRESS|SCIPY|CUSTOM;
    cvx_custom_solver MODULE;
    cvx_warm_start FALSE|TRUE;
    cvx_solver_options KEY:VALUE[,...];
    cvx_infeasible HALT|WARN|IGNORE;
}
object cvx
{
    event {NONE,INIT,PRECOMMIT,PRESYNC,SYNC,POSTSYNC,COMMIT,FINALIZE};
    data NAME:[OBJECT|CLASS|GROUP].PROPERTY[,...];
    variables NAME=GLOBAL[/DUAL][,...];
    variables NAME=GROUP@PROPERTY[/DUAL][,...];
    variables NAME=CLASS:PROPERTY[/DUAL][,...];
    variables NAME=OBJECT.PROPERTY[/DUAL][,...];
    objective [min|max](EXPRESSION);
    constraints EXPRESSION[:OBJECT.PROPERTY][,...];
    value FLOAT;
}
~~~

# Description

The `cvx` object sets up a convex optimization using CVXPY.  The optimization is run on any event included in the `event` set.  

Zero of more `data` references can be provided. References to objects are
singletons and references to groups and classes are vectors comprising all
members of the group or class. The `data` vector is assembled from the
specified values in the order which they are received. Classes and groups are
ordered by object id. 

One or more `variables` may be specified in the same manner as `data` definitions. If the dual is specified, it uses the same aggregation as the primal property, e.g., `x=CLASS:PRIMAL/DUAL` will use `PRIMAL` as the primal variable and `DUAL` as the dual variable in all object of `CLASS`. 

Note: when the problem is infeasible or unbounded the variables are not updated and the object properties are unchanged from the previous values.

When the optimization is successful, the value of the objective function is stored in the `value`. If the problem is infeasible, `value` is `inf`. If the problem is unbounded `value` if `-inf`.

# Caveat

It is often important to establish the correct rank for an optimizer so that it runs after all the objects it depends on have updated their properties. Use the `parent` property to ensure that the optimizer is initialized after all the objects it depends on.

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