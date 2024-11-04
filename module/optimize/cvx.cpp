// module/optimize/cvx.cpp

#include "cvx.h"

EXPORT_CREATE(cvx);
EXPORT_INIT(cvx);
EXPORT_PRECOMMIT(cvx);
EXPORT_SYNC(cvx);
EXPORT_COMMIT(cvx);
EXPORT_FINALIZE(cvx);

EXPORT_METHOD(cvx,data)
EXPORT_METHOD(cvx,variables)
EXPORT_METHOD(cvx,objective)
EXPORT_METHOD(cvx,constraints)

CLASS *cvx::oclass = NULL;
cvx *cvx::defaults = NULL;

//
// Global variables
//

enumeration cvx::backend = cvx::BE_CPP;
set cvx::options = cvx::CO_NONE;
enumeration cvx::dpp = cvx::CD_DEFAULT;
enumeration cvx::solver = cvx::CS_AUTO;
char1024 cvx::custom_solver = "";
bool cvx::warm_start = false;
char1024 cvx::solver_options = "";
enumeration cvx::failure_handling = cvx::OF_HALT;
PyObject *cvx::main_module = NULL;
PyObject *cvx::globals = NULL;
char1024 cvx::imports = "";
char1024 cvx::problemdump = "";

//
// Python Run function with formatting
//

int PyRun_FormatString(const char *format, ...)
{
    va_list ptr;
    va_start(ptr,format);
    char *buffer;
    vasprintf(&buffer,format,ptr);
    gl_verbose("Running python command '%s'",buffer);
    int result = PyRun_SimpleString(buffer);
    if ( result != 0 )
    {
        gl_verbose("Python command failed!");
    }
    free(buffer);
    va_end(ptr);
    return result;
}

//
// CVX class creation
//

cvx::cvx(MODULE *module)
{
    if (oclass==NULL)
    {
        // register to receive notice for first top down. bottom up, and second top down synchronizations
        oclass = gld_class::create(module,"cvx",sizeof(cvx),PC_PRETOPDOWN|PC_BOTTOMUP|PC_POSTTOPDOWN|PC_AUTOLOCK|PC_OBSERVER);
        if (oclass==NULL)
            throw "unable to register class cvx";
        else
            oclass->trl = TRL_PROVEN;

        defaults = this;
        if (gl_publish_variable(oclass,

            PT_set, "event", get_event_offset(),
                PT_DEFAULT, "NONE",
                PT_KEYWORD, "INIT", (set)OE_INIT,
                PT_KEYWORD, "PRECOMMIT", (set)OE_PRECOMMIT,
                PT_KEYWORD, "PRESYNC", (set)OE_PRESYNC,
                PT_KEYWORD, "SYNC", (set)OE_SYNC,
                PT_KEYWORD, "POSTSYNC", (set)OE_POSTSYNC,
                PT_KEYWORD, "COMMIT", (set)OE_COMMIT,
                PT_KEYWORD, "FINALIZE", (set)OE_FINALIZE,
                PT_KEYWORD, "NONE", (set)OE_NONE,
                PT_DESCRIPTION, "event during which the optimization problem should be solved",

            PT_char1024, "presolve", get_presolve_offset(),
                PT_DESCRIPTION, "presolve script",

            PT_char1024, "postsolve", get_postsolve_offset(),
                PT_DESCRIPTION, "postsolve script",

            PT_char1024, "on_failure", get_on_failure_offset(),
                PT_DESCRIPTION, "on_failure script",

            PT_char1024, "on_exception", get_on_exception_offset(),
                PT_DESCRIPTION, "on_exception script",

            PT_char1024, "on_infeasible", get_on_infeasible_offset(),
                PT_DESCRIPTION, "on_infeasible script",

            PT_char1024, "on_unbounded", get_on_unbounded_offset(),
                PT_DESCRIPTION, "on_unbounded script",

            PT_method, "data", get_data_offset(),
                PT_DESCRIPTION, "problem data definition",

            PT_method, "variables", get_variables_offset(),
                PT_DESCRIPTION, "problem variable definitions",
                
            PT_method, "objective", get_objective_offset(),
                PT_REQUIRED,
                PT_DESCRIPTION, "problem objective expression",
                
            PT_method, "constraints", get_constraints_offset(),
                PT_DESCRIPTION, "problem constraint expressions",
            
            PT_double, "value", get_value_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "optimal value",    

            NULL)<1)
        {
            exception("unable to publish optimize/cvx properties");
        }

        gl_global_create("optimize::cvx_backend",PT_enumeration,&backend,
            PT_KEYWORD, "CPP", (enumeration)BE_CPP,
            PT_KEYWORD, "SCIPY", (enumeration)BE_SCIPY,
            PT_KEYWORD, "NUMPY", (enumeration)BE_NUMPY,
            PT_DESCRIPTION,"CVX backend implementation",NULL);

        gl_global_create("optimize::cvx_options",PT_set,&options,
            PT_KEYWORD, "VERBOSE", (set)CO_VERBOSE,
            PT_KEYWORD, "GP", (set)CO_GP,         
            PT_KEYWORD, "QCP", (set)CO_QCP,
            PT_KEYWORD, "GRADIENTS", (set)CO_GRADIENTS,
            PT_KEYWORD, "NONE", (set)CO_NONE,
            PT_DESCRIPTION,"CVX options",NULL);

        gl_global_create("optimize::cvx_dpp",PT_enumeration,&dpp,
            PT_KEYWORD, "DEFAULT", (enumeration)CD_DEFAULT,
            PT_KEYWORD, "ENFORCE", (enumeration)CD_ENFORCE,
            PT_KEYWORD, "IGNORE", (enumeration)CD_IGNORE,
            PT_DESCRIPTION,"CVX DPP enforcement",NULL);

        gl_global_create("optimize::cvx_solver",PT_enumeration,&solver,
            PT_KEYWORD, "AUTO", CS_AUTO,
            PT_KEYWORD, "CBC", CS_CBC,
            PT_KEYWORD, "CLARABEL", CS_CLARABEL,
            PT_KEYWORD, "COPT", CS_COPT,
            PT_KEYWORD, "DAQP", CS_DAQP,
            PT_KEYWORD, "GLOP", CS_GLOP,
            PT_KEYWORD, "GLPK", CS_GLPK,
            PT_KEYWORD, "GLPK_MI", CS_GLPK_MI,
            PT_KEYWORD, "OSQP", CS_OSQP,
            PT_KEYWORD, "PIQP", CS_PIQP,
            PT_KEYWORD, "PROXQP", CS_PROXQP,
            PT_KEYWORD, "PDLP", CS_PDLP,
            PT_KEYWORD, "CPLEX", CS_CPLEX,
            PT_KEYWORD, "NAG", CS_NAG,
            PT_KEYWORD, "ECOS", CS_ECOS,
            PT_KEYWORD, "GUROBI", CS_GUROBI,
            PT_KEYWORD, "MOSEK", CS_MOSEK,
            PT_KEYWORD, "CVXOPT", CS_CVXOPT,
            PT_KEYWORD, "DSPA", CS_DSPA,
            PT_KEYWORD, "SCS", CS_SCS,
            PT_KEYWORD, "SCIP", CS_SCIP,
            PT_KEYWORD, "XPRESS", CS_XPRESS,
            PT_KEYWORD, "SCIPY", CS_SCIPY,
            PT_KEYWORD, "CUSTOM", CS_CUSTOM,
            PT_DESCRIPTION,"CVX solver selection",NULL);

        gl_global_create("optimize::cvx_custom_solver",PT_char1024,&custom_solver,
            PT_DESCRIPTION, "CVX custom solver module pathname", NULL);

        gl_global_create("optimize::cvx_warm_start",PT_bool,&warm_start,
            PT_DESCRIPTION, "enable CVX solver warm-start functionality",NULL);

        gl_global_create("optimize::cvx_solver_options",PT_char1024,&solver_options,
            PT_DESCRIPTION, "CVX solver-specification options", NULL);

        gl_global_create("optimize::cvx_failure_handling",PT_enumeration,&failure_handling,
            PT_KEYWORD, "HALT", OF_HALT,
            PT_KEYWORD, "WARN", OF_WARN,
            PT_KEYWORD, "IGNORE", OF_IGNORE,
            PT_DESCRIPTION, "CVX failure handling", NULL);

        gl_global_create("optimize::cvx_imports",PT_char1024,&imports,
            PT_DESCRIPTION, "CVX symbols to import", NULL);

        gl_global_create("optimize::cvx_problemdump",PT_char1024,&problemdump,
            PT_DESCRIPTION, "CVX problem dump filename", NULL);

        main_module = PyImport_AddModule("__main__");
        if ( main_module == NULL )
        {
            exception("unable to access python __main__ module");
        }

        globals = PyModule_GetDict(main_module);
        if ( globals == NULL )
        {
            exception("unable to access python globals in __main__");
        }

        // create __cvx__ global
        PyDict_SetItemString(globals,"__cvx__",PyDict_New());
    }
}

//
// CVX Object creation
//

int cvx::create(void) 
{
    // initialize properties
    set_event(OE_NONE);
    set_presolve("");
    set_postsolve("");
    set_on_failure("");
    set_on_exception("");
    set_on_infeasible("");
    set_on_unbounded("");
    set_value(QNAN);

    // setup problem data
    problem.objective = strdup("");
    problem.data = NULL;
    problem.variables = NULL;
    problem.constraints = NULL;

    // load python modules if needed
    if ( PyDict_GetItemString(globals,"cvx") == NULL )
    {
        // load cvxpy module
        cvxpy = PyImport_ImportModule("cvxpy");
        if ( cvxpy == NULL )
        {
            if ( PyErr_Occurred() )
            {
                PyErr_Print();
            }
            exception("unable to load cvxpy module");
        }

        // import cvxpy module
        if ( PyRun_FormatString("import cvxpy as cvx") != 0 )
        {
            exception("unable to import cvxpy");
        }

        // import requested definitions from cvxpy, if any
        if ( strcmp(imports,"") != 0 && PyRun_FormatString("from cvxpy import %s", (const char*)imports) != 0 )
        {
            exception("unable to import cvxpy symbols");
        }

        // import numpy
        if ( PyRun_FormatString("import numpy as np") != 0 )
        {
            exception("unable to load numpy");
        }
    }

    return 1; /* return 1 on success, 0 on failure */
}

//
// CVX Object initialization
//

int cvx::init(OBJECT *parent)
{
    // setup problem dump
    if ( PyDict_GetItemString(globals,"__dump__") == NULL )
    {
        gld_clock now;
        if ( strcmp(problemdump,"") == 0 )
        {
            PyRun_FormatString("__dump__ = None");
        }
        else if ( PyRun_FormatString("__dump__ = open('%s','w'); print('Problem dumps starting at t=%lld (%s)\\n',file=__dump__,flush=True);",(const char*)problemdump,gl_globalclock,now.get_string().get_buffer()) < 0 )
        {
            exception("unable to open dumpfile '%s'",(const char*)problemdump);
        }
    }

    // objective must be specified
    if ( strlen(problem.objective) == 0 )
    {
        exception("missing problem objective");
    }

    // create this optimizers data in __cvx__ global
    PyDict_SetItemString(PyDict_GetItemString(globals,"__cvx__"),(const char*)get_name(),PyDict_New());

    // initialization solution event handler
    if ( get_event(OE_INIT) && ! update_solution(problem) )
    {
        // warn on failure if required
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during init event");
        }

        // handle failure
        return failure_handling != OF_HALT ? 1 : 0;
    }

    if ( get_event() == OE_NONE )
    {
        warning("problem has no event handler specified and will never be solved");
    }

    return 1; // should use deferred optimization until all input objects are initialized
}

// 
// Event handlers
//

int cvx::precommit(TIMESTAMP t0)
{
    if ( get_event(OE_PRECOMMIT) && ! update_solution(problem) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during precommit event");
        }
        return failure_handling != OF_HALT ? 1 : 0;
    }
    return 1;
}

TIMESTAMP cvx::presync(TIMESTAMP t0)
{
    if ( get_event(OE_PRESYNC) && ! update_solution(problem) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during presync event");
        }
        return failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

TIMESTAMP cvx::sync(TIMESTAMP t0)
{
    if ( get_event(OE_SYNC) && ! update_solution(problem) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during sync event");
        }
        return failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

TIMESTAMP cvx::postsync(TIMESTAMP t0)
{
    if ( get_event(OE_POSTSYNC) && ! update_solution(problem) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during postsync event");
        }
        return failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

TIMESTAMP cvx::commit(TIMESTAMP t0,TIMESTAMP t1)
{
    if ( get_event(OE_COMMIT) )
    {
        if ( failure_handling == OF_WARN && ! update_solution(problem) )
        {
            warning("optimization failed during commit event");
        }
        return failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

int cvx::finalize(void)
{
    if ( get_event(OE_FINALIZE) && ! update_solution(problem) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during finalize event");
        }
        return failure_handling != OF_HALT ? 1 : 0;
    }
    return 1;
}

//
// Data request
// 

int cvx::data(
    char *buffer, // read/write buffer (NULL for size check/request)
    size_t len // write buffer len (0 for read request or size check)
    )
{
    if ( buffer == NULL ) // compute size of write request
    {
        int result = 0;
        for ( DATA *item = problem.data ; item != NULL ; item = item->next )
        {
            result += strlen(item->spec) + ( result > 0 ? 1 : 0 );
        }
        if ( len == 0 )
        {
            // return length of result only
            return result;
        }
        else
        {
            // return non-zero if len > length of result
            return (int)len > result ? result : 0;
        }
    }
    else if ( len == 0 ) // read buffer into object data
    {
        // return number of characters read from buffer
        return add_data(problem,buffer) ? strlen(buffer) : 0;
    }
    else // write object data into buffer
    {
        int result = 0;
        for ( DATA *item = problem.data ; item != NULL ; item = item->next )
        {
            result += snprintf(buffer+result,len-result,"%s%s",result>0?";":"",item->spec);
        }
        // return number of characters written to buffer
        return result;
    }
}

//
// Variable request
//

int cvx::variables(
    char *buffer, // read/write buffer (NULL for size request)
    size_t len // write buffer len (0 for read request or size check)
    )
{
    if ( buffer == NULL ) // compute size of write request
    {
        int result = 0;
        for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
        {
            result += strlen(item->spec) + ( result > 0 ? 1 : 0 );
        }
        if ( len == 0 )
        {
            // return length of result only
            return result;
        }
        else
        {
            // return non-zero if len > length of result
            return (int)len > result ? result : 0;
        }
    }
    else if ( len == 0 ) // read buffer into object data
    {
        // return number of characters read from buffer
        return add_variables(problem,buffer) ? strlen(buffer) : 0;
    }
    else // write object data into buffer
    {
        int result = 0;
        for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
        {
            result += snprintf(buffer+result,len-result,"%s%s",result>0?";":"",item->spec);
        }
        // return number of characters written to buffer
        return result;
    }
}

//
// Objective request
//

int cvx::objective(
    char *buffer, // read/write buffer (NULL for size request)
    size_t len // write buffer len (0 for read request or size check)
    )
{
    if ( buffer == NULL ) // compute size of write request
    {
        size_t result = strlen(problem.objective);
        if ( len == 0 )
        {
            // return length of result only
            return result;
        }
        else
        {
            // return non-zero if len > length of result
            return len>result ? result : 0;
        }
    }
    else if ( len == 0 ) // read buffer into object data
    {
        // return number of characters read from buffer
        return set_objective(problem,buffer) ? strlen(problem.objective) : 0;
    }
    else // write object data into buffer
    {
        // return number of characters written to buffer
        return snprintf(buffer,len,"%s",problem.objective);
    }
}

//
// Constraint request
//

int cvx::constraints(
    char *buffer, // read/write buffer (NULL for size request)
    size_t len // write buffer len (0 for read request or size check)
    )    
{
    if ( buffer == NULL ) // compute size of write request
    {
        int result = 0;
        for ( CONSTRAINT *item = problem.constraints ; item != NULL ; item = item->next )
        {
            result += strlen(item->spec) + ( result > 0 ? 1 : 0 );
        }
        if ( len == 0 )
        {
            // return length of result only
            return result;
        }
        else
        {
            // return non-zero if len > length of result
            return (int)len > result ? result : 0;
        }
    }
    else if ( len == 0 ) // read buffer into object data
    {
        // return number of characters read from buffer
        return add_constraints(problem,buffer) ? strlen(buffer) : 0;
    }
    else // write object data into buffer
    {
        int result = 0;
        for ( CONSTRAINT *item = problem.constraints ; item != NULL ; item = item->next )
        {
            result += snprintf(buffer+result,len-result,"%s%s",result>0?",":"",item->spec);
        }
        // return number of characters written to buffer
        return result;
    }
}

//
// Link object properties to CVX data
//

bool cvx::add_data(struct s_problem &problem, const char *spec)
{
    if ( strchr(spec,';') != NULL )
    {
        char *buffer = strdup(spec);
        if ( buffer == NULL )
        {
            exception("memory allocation error");
            return false;
        }
        char *item, *next = buffer;
        while ( (item=strsep(&next,";")) != NULL )
        {
            if ( ! add_variables(problem,item) )
            {
                free(buffer);
                return false;
            }
        }
        free(buffer);
        return true;
    }
    else
    {
        DATA *item = (DATA*)malloc(sizeof(DATA));
        if ( item == NULL )
        {
            exception("memory allocation error");
        }
        item->spec = strdup(spec);
        if ( item->spec == NULL )
        {
            exception("memory allocation error");
        }
        char *buffer = strdup(spec);
        if ( buffer == NULL )
        {
            exception("memory allocation error");
        }
        char *speclist = buffer;
        item->name = strdup(strsep(&speclist,"="));
        if ( item->name == NULL )
        {
            exception("memory allocation error");
        }
        if ( speclist == NULL )
        {
            exception("variable specification '%s' missing expected '='", buffer);
        }
        item->data = NULL;
        item->list = PyList_New(0);
        if ( item->list == NULL )
        {
            exception("memory allocation error");
        }

        // check for duplicate specification
        for ( DATA *var = problem.data ; var != NULL ; var = var->next )
        {
            if ( strcmp(var->name,item->name) == 0 )
            {
                exception("variable '%s' already specified, ignoring duplicate definition",item->name);
            }
        }

        // link properties
        char *varspec;
        while (  (varspec=strsep(&speclist,",")) != NULL )
        {
            char classname[65], groupname[65], objectname[65], primalname[65], dualname[65] = "";
            // fprintf(stderr,"scanning '%s' for a valid property spec...\n",varspec);
            if ( sscanf(varspec,"%[^:]:%[^&]&%[^,]",classname,primalname,dualname) >= 2 )
            {
                // gld_class oclass(classname);
                // gld_property *primalprop = oclass.get_property(primalname,true);
                CLASS *oclass = gl_class_get_by_name(classname,NULL);
                int count = 0;
                for ( OBJECT *obj = gl_object_get_first() ; obj != NULL ; obj = obj->next )
                {
                    if ( obj->oclass == oclass )
                    {
                        // TODO: link property to list
                        gl_warning("TODO: item %d class '%s' object '%s' primal '%s' dual '%s'",count,classname,get_object(obj)->get_name(),primalname,dualname);
                        count++;
                    }
                }
                if ( count == 0 )
                {
                    warning("class '%s' has no objects",classname);
                }
            }
            else if ( sscanf(varspec,"%[^@]@%[^/]/%[^,]",groupname,primalname,dualname) >= 2 )
            {
                int count = 0;
                for ( OBJECT *obj = gl_object_get_first() ; obj != NULL ; obj = obj->next )
                {
                    if ( strcmp(obj->groupid,groupname) == 0 )
                    {
                        // TODO: link property to list
                        gl_warning("TODO: item %d group '%s' object '%s' primal '%s' dual '%s'",count,groupname,get_object(obj)->get_name(),primalname,dualname);
                        count++;
                    }
                }
                if ( count == 0 )
                {
                    warning("group '%s' has no objects",groupname);
                }
            }
            else if ( sscanf(varspec,"%[^.].%[^&]&%[^,]",objectname,primalname,dualname) >= 2 )
            {
                gl_warning("TODO: object '%s' primal '%s' dual '%s'",objectname,primalname,dualname);
            }
            else if ( sscanf(varspec,"%[^&]&%[^,]",primalname,dualname) >= 1 )
            {
                gl_warning("TODO: global primal '%s' dual '%s'",primalname,dualname);
            }
            else
            {
                exception("ignoring invalid variable spec '%s'",varspec);
            }
        }

        // link to list
        item->next = problem.data;
        problem.data = item;
        free(buffer);
        return true;
    }
}

//
// Link object properties to CVX variable
//

bool cvx::add_variables(struct s_problem &problem, const char *spec)
{
    if ( strchr(spec,';') != NULL )
    {
        char *buffer = strdup(spec);
        if ( buffer == NULL )
        {
            exception("memory allocation error");
            return false;
        }
        char *item, *next = buffer;
        while ( (item=strsep(&next,";")) != NULL )
        {
            if ( ! add_variables(problem,item) )
            {
                free(buffer);
                return false;
            }
        }
        free(buffer);
        return true;
    }
    else
    {
        VARIABLE *item = (VARIABLE*)malloc(sizeof(VARIABLE));
        if ( item == NULL )
        {
            exception("memory allocation error");
        }
        item->spec = strdup(spec);
        if ( item->spec == NULL )
        {
            exception("memory allocation error");
        }
        char *buffer = strdup(spec);
        if ( buffer == NULL )
        {
            exception("memory allocation error");
        }
        char *speclist = buffer;
        item->name = strdup(strsep(&speclist,"="));
        if ( item->name == NULL )
        {
            exception("memory allocation error");
        }
        if ( speclist == NULL )
        {
            exception("variable specification '%s' missing expected '='", buffer);
        }
        item->primal = NULL;
        item->dual = NULL;
        item->count = 0;

        // check for duplicate specification
        for ( VARIABLE *var = problem.variables ; var != NULL ; var = var->next )
        {
            if ( strcmp(var->name,item->name) == 0 )
            {
                exception("variable '%s' already specified, ignoring duplicate definition",item->name);
            }
        }

        // link properties
        char *varspec;
        while (  (varspec=strsep(&speclist,",")) != NULL )
        {
            char classname[65], groupname[65], objectname[65], primalname[65], dualname[65] = "";
            // fprintf(stderr,"scanning '%s' for a valid property spec...\n",varspec);
            if ( sscanf(varspec,"%[^:]:%[^&]&%[^,]",classname,primalname,dualname) >= 2 )
            {
                // gld_class oclass(classname);
                // gld_property *primalprop = oclass.get_property(primalname,true);
                CLASS *oclass = gl_class_get_by_name(classname,NULL);
                for ( OBJECT *obj = gl_object_get_first() ; obj != NULL ; obj = obj->next )
                {
                    if ( obj->oclass == oclass )
                    {
                        gld_property data(obj,primalname);
                        if ( ! data.is_valid() )
                        {
                            exception("primal property '%s' is not valid",primalname);
                        }
                        if ( ! data.is_double() )
                        {
                            exception("primal property '%s' is not a real number",primalname);
                        }
                        REFERENCE *primal = new REFERENCE;
                        if ( primal == NULL )
                        {
                            exception("memory allocation error");
                        }
                        primal->ref = (double*)data.get_addr();
                        primal->next = item->primal;
                        item->primal = primal;
                        item->count++;
                    }
                }
                if ( item->count == 0 )
                {
                    warning("class '%s' has no objects",classname);
                }
            }
            else if ( sscanf(varspec,"%[^@]@%[^/]/%[^,]",groupname,primalname,dualname) >= 2 )
            {
                int count = 0;
                for ( OBJECT *obj = gl_object_get_first() ; obj != NULL ; obj = obj->next )
                {
                    if ( strcmp(obj->groupid,groupname) == 0 )
                    {
                        // TODO: link property to list
                        gl_warning("TODO: item %d group '%s' object '%s' primal '%s' dual '%s'",count,groupname,get_object(obj)->get_name(),primalname,dualname);
                        count++;
                    }
                }
                if ( count == 0 )
                {
                    warning("group '%s' has no objects",groupname);
                }
            }
            else if ( sscanf(varspec,"%[^.].%[^&]&%[^,]",objectname,primalname,dualname) >= 2 )
            {
                gl_warning("TODO: object '%s' primal '%s' dual '%s'",objectname,primalname,dualname);
            }
            else if ( sscanf(varspec,"%[^&]&%[^,]",primalname,dualname) >= 1 )
            {
                gl_warning("TODO: global primal '%s' dual '%s'",primalname,dualname);
            }
            else
            {
                exception("ignoring invalid variable spec '%s'",varspec);
            }
        }

        // link to list
        item->next = problem.variables;
        problem.variables = item;
        free(buffer);
        return true;
    }
}

//
// Add a problem constraint
//

bool cvx::add_constraints(struct s_problem &problem, const char *spec)
{
    CONSTRAINT *item = (CONSTRAINT*)malloc(sizeof(CONSTRAINT));
    if ( item == NULL )
    {
        exception("memory allocation error");
        return false;
    }
    item->spec = strdup(spec);
    if ( item->spec == NULL )
    {
        exception("memory allocation error");
        return false;
    }
    item->next = problem.constraints;
    problem.constraints = item;
    return true;
}

//
// Set problem objective
//

bool cvx::set_objective(struct s_problem &problem, const char *spec)
{
    free(problem.objective);
    problem.objective = strdup(spec);
    if ( problem.objective == NULL )
    {
        exception("memory allocation error");
        return false;
    }
    return true;
}

//
// Update solution to problem
//

bool cvx::update_solution(struct s_problem &problem)
{
    const char *optname = (const char *)get_name();
    bool status = true;

    verbose("updating problem");

    if ( strcmp(presolve,"") != 0 )
    {
        PyRun_FormatString(presolve);
    }
    for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
    {
        if ( PyRun_FormatString("%s = cvx.Variable(%ld)",item->name,item->count) == -1 )
        {
            exception("unable to create CVX variable '%s'",item->name);
        }
        else
        {
            verbose("variable '%s' created with length %ld",item->name,item->count);
        }
    }


    if ( PyRun_FormatString("__cvx__['%s']['objective'] = %s",optname,problem.objective) == -1 )
    {
        exception("objective specification '%s' is invalid",problem.objective);
    }

    char buffer[1024];
    if ( PyRun_FormatString("__cvx__['%s']['constraints'] = [%s]",optname,constraints(buffer,sizeof(buffer)-1)>0?buffer:"") == -1 )
    {
        exception("constraints specification '[%s]' is invalid",buffer);
    }

    if ( PyRun_FormatString("__cvx__['%s']['problem'] = cvx.Problem(__cvx__['%s']['objective'],__cvx__['%s']['constraints'])",optname,optname,optname) == -1 )
    {
        if ( strcmp(on_failure,"") != 0 )
        {
            PyRun_FormatString(on_failure);
        }
        exception("problem construction failed");
    }

    if ( strcmp(problemdump,"") != 0 )
    {
        gld_clock now;
        PyRun_FormatString("print('*** Problem \\'%s\\' at t=%lld (%s) ***\\n',file=__dump__)",optname,gl_globalclock,now.get_string().get_buffer());
        PyRun_FormatString("print('Objective:',__cvx__['%s']['objective'],file=__dump__)",optname);
        PyRun_FormatString("print('Contraints:',__cvx__['%s']['constraints'],file=__dump__)",optname);
    }

    if ( PyRun_FormatString("__cvx__['%s']['value'] = __cvx__['%s']['problem'].solve()",optname,optname) == -1 )
    {
        if ( strcmp(problemdump,"") != 0 )
        {
            // PyRun_FormatString("print('\\n'.join([f'{x}: {y}' for x,y in __problem__.get_problem_data(__problem__.solver_stats.solver_name)[0].items()]),file=__dump__,flush=True)");
            PyRun_FormatString("print('Problem rejected',file=__dump__,flush=True)");
        }
        if ( strcmp(on_exception,"") != 0 )
        {
            PyRun_FormatString(on_exception);
        }
        exception("problem solve failed");
    }

    if ( strcmp(problemdump,"") != 0 )
    {
        PyRun_FormatString("print('\\n'.join([f'{x}: {y}' for x,y in __cvx__['%s']['problem'].get_problem_data(__cvx__['%s']['problem'].solver_stats.solver_name)[0].items()]),file=__dump__)",optname,optname);
    }

    PyObject *cvx = PyDict_GetItemString(globals,"__cvx__");
    PyObject *value = PyDict_GetItemString(PyDict_GetItemString(cvx,optname),"value");
    this->value = PyFloat_AsDouble(value);
    if ( ! isfinite(this->value) )
    {
        if ( this->value < 0 )
        {            
            if ( strcmp(problemdump,"") != 0 )
            {
                PyRun_FormatString("print('Problem is unbounded\\n',file=__dump__,flush=True)");
            }
            if ( strcmp(on_unbounded,"") != 0 )
            {
                PyRun_FormatString(on_unbounded);
            }
        }
        else
        {
            if ( strcmp(problemdump,"") != 0 )
            {
                PyRun_FormatString("print('Problem is infeasible\\n,file=__dump__,flush=True)");
            }
            if ( strcmp(on_infeasible,"") != 0 )
            {
                PyRun_FormatString(on_infeasible);
            }
        }
        switch (failure_handling)
        {
        case OF_HALT:
            error("problem is %s",this->value>0?"infeasible":"unbounded");
            break;
        case OF_WARN:
            warning("problem is %s",this->value>0?"infeasible":"unbounded");
            break;
        case OF_IGNORE:
            verbose("ignoring %s problem",this->value>0?"infeasible":"unbounded");
            break;
        default:
            exception("invalid handling (failure_handling=%ld) for %s problem",failure_handling,this->value>0?"infeasible":"unbounded");
            break;
        }
        status = false;
    }
    else
    {
        if ( strcmp(problemdump,"") != 0 )
        {
            PyRun_FormatString("print('Problem solved: objective value is','{0:.6g}'.format(__cvx__['%s']['problem'].value),file=__dump__,flush=True)",optname);
        }

        char buffer[65536];
        int len = snprintf(buffer,sizeof(buffer)-1,"__cvx__['%s']['result'] = {",optname);
        for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
        {
            len += snprintf(buffer+len,sizeof(buffer)-len-1,"'%s':%s.value.tolist() if not %s.value is None else [],",
                item->name,item->name,item->name);
        }
        len += snprintf(buffer+len,sizeof(buffer)-len-1,"%s","}\n");
        if ( PyRun_FormatString(buffer) < 0 )
        {
            exception("unable to get result");
        }

        if ( strcmp(postsolve,"") != 0 )
        {
            PyRun_FormatString(postsolve);
        }

        PyObject *result = PyDict_GetItemString(PyDict_GetItemString(cvx,optname),"result");
        for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
        {
            PyObject *var = PyDict_GetItemString(result,item->name);
            Py_ssize_t ndx = 0;
            for ( REFERENCE *prop = item->primal ; prop != NULL ; prop = prop->next )
            {
                *(prop->ref) = PyFloat_AsDouble(PyList_GetItem(var,ndx++));
            }
        }
        if ( strcmp(problemdump,"") != 0 )
        {
            PyRun_FormatString("print('Result:',__cvx__['%s']['result'],'\\n',file=__dump__,flush=True)",optname);
        }
        status = true;
    }

    return status;
}

