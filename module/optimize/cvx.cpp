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

int PyRun_FormatString(const char *format, ...)
{
    va_list ptr;
    va_start(ptr,format);
    char *buffer;
    vasprintf(&buffer,format,ptr);
    int result = PyRun_SimpleString(buffer);
    free(buffer);
    va_end(ptr);
    return result;
}

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

        gl_global_create("optimize::failure_handling",PT_enumeration,&failure_handling,
            PT_KEYWORD, "HALT", OF_HALT,
            PT_KEYWORD, "WARN", OF_WARN,
            PT_KEYWORD, "IGNORE", OF_IGNORE,
            PT_DESCRIPTION, "CVX failure handling", NULL);

        gl_global_create("optimize::cvx_imports",PT_char1024,&imports,
            PT_DESCRIPTION, "CVX symbols to import", NULL);

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
    }
}

int cvx::create(void) 
{
    set_event(OE_NONE);
    set_presolve("");
    set_postsolve("");
    set_on_failure("");
    set_on_exception("");
    set_on_infeasible("");
    set_on_unbounded("");
    problem.objective = strdup("");
    problem.data = NULL;
    problem.variables = NULL;
    problem.constraints = NULL;
    cvxpy = PyImport_ImportModule("cvxpy");
    if ( cvxpy == NULL )
    {
        if ( PyErr_Occurred() )
        {
            PyErr_Print();
        }
        exception("unable to load cvxpy module");
    }

    if ( PyRun_SimpleString("import cvxpy as cvx") != 0 )
    {
        exception("unable to import cvxpy");
    }

    if ( strcmp(imports,"") != 0 && PyRun_FormatString("from cvxpy import %s", (const char*)imports) != 0 )
    {
        exception("unable to import cvxpy symbols");
    }

    if ( PyRun_SimpleString("import numpy as np") != 0 )
    {
        exception("unable to load numpy");
    }
    return 1; /* return 1 on success, 0 on failure */
}

int cvx::init(OBJECT *parent)
{
    if ( strlen(problem.objective) == 0 )
    {
        exception("missing problem objective");
    }

    if ( get_event(OE_INIT) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during init event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? 1 : 0;
    }
    return 1; // should use deferred optimization until all input objects are initialized
}

int cvx::precommit(TIMESTAMP t0)
{
    if ( get_event(OE_PRECOMMIT) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during precommit event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? 1 : 0;
    }
    return 1;
}

TIMESTAMP cvx::presync(TIMESTAMP t0)
{
    if ( get_event(OE_PRESYNC) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during presync event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

TIMESTAMP cvx::sync(TIMESTAMP t0)
{
    if ( get_event(OE_SYNC) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during sync event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

TIMESTAMP cvx::postsync(TIMESTAMP t0)
{
    if ( get_event(OE_POSTSYNC) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during postsync event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

TIMESTAMP cvx::commit(TIMESTAMP t0,TIMESTAMP t1)
{
    if ( get_event(OE_COMMIT) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during commit event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? TS_NEVER : TS_INVALID;
    }
    return TS_NEVER;
}

int cvx::finalize(void)
{
    if ( get_event(OE_FINALIZE) )
    {
        if ( failure_handling == OF_WARN )
        {
            warning("optimization failed during finalize event");
        }
        return update_solution(problem) || failure_handling != OF_HALT ? 1 : 0;
    }
    return 1;
}

int cvx::data(char *buffer, size_t len)
{
    if ( buffer == NULL )
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
    else if ( len == 0 )
    {
        // return number of characters read from buffer
        return add_data(problem,buffer) ? strlen(buffer) : 0;
    }
    else
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

int cvx::variables(char *buffer, size_t len)
{
    if ( buffer == NULL )
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
    else if ( len == 0 )
    {
        // return number of characters read from buffer
        return add_variables(problem,buffer) ? strlen(buffer) : 0;
    }
    else
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

int cvx::objective(char *buffer, size_t len)
{
    if ( buffer == NULL )
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
    else if ( len == 0 )
    {
        // return number of characters read from buffer
        return set_objective(problem,buffer) ? strlen(problem.objective) : 0;
    }
    else
    {
        // return number of characters written to buffer
        return snprintf(buffer,len,"%s",problem.objective);
    }
}

int cvx::constraints(char *buffer, size_t len)
{
    if ( buffer == NULL )
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
    else if ( len == 0 )
    {
        // return number of characters read from buffer
        return add_constraints(problem,buffer) ? strlen(buffer) : 0;
    }
    else
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

bool cvx::add_data(struct s_problem &problem, const char *spec)
{
    DATA *item = (DATA*)malloc(sizeof(DATA));
    if ( item == NULL )
    {
        exception("memory allocation error");
        return false;
    }
    item->spec = strdup(spec);
    char *buffer = strdup(spec);
    item->name = strsep(&buffer,"=");
    if ( buffer == NULL )
    {
        error("data specification missing expected '='");
        return false;
    }
    item->next = problem.data;
    problem.data = item;
    return true;
}

bool cvx::add_variables(struct s_problem &problem, const char *spec)
{
    if ( strchr(spec,',') != NULL )
    {
        char *buffer = strdup(spec);
        if ( buffer == NULL )
        {
            exception("memory allocation error");
            return false;
        }
        char *item, *next = buffer;
        while ( (item=strsep(&next,",")) != NULL )
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
            return false;
        }
        item->spec = strdup(spec);
        if ( item->spec == NULL )
        {
            exception("memory allocation error");
            free(item);
            return false;
        }
        char *buffer = strdup(spec);
        if ( buffer == NULL )
        {
            exception("memory allocation error");
            free(item->spec);
            free(item);
            return false;
        }
        char *speclist = buffer;
        item->name = strdup(strsep(&speclist,"="));
        if ( item->name == NULL )
        {
            exception("memory allocation error");
            free(item->spec);
            free(item);
            free(buffer);
            return false;
        }
        if ( speclist == NULL )
        {
            error("variable specification '%s' missing expected '='", buffer);
            return false;
        }
        item->data = NULL;
        item->list = PyList_New(0);
        if ( item->list == NULL )
        {
            exception("memory allocation error");
            free(item->spec);
            free(item->name);
            free(item);
            free(buffer);
            return false;
        }

        // link properties
        try
        {
            // check for duplicate specification
            for ( VARIABLE *var = problem.variables ; var != NULL ; var = var->next )
            {
                if ( strcmp(var->name,item->name) == 0 )
                {
                    exception("variable '%s' already specified, ignoring duplicate definition",item->name);
                }
            }

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
        }
        catch ( const char *err )
        {
            error(err);
            free(item->spec);
            free(item->name);
            free(item);
            free(buffer);
            return false;
        }

        // link to list
        item->next = problem.variables;
        problem.variables = item;
        free(buffer);
        return true;
    }
}

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

bool cvx::update_solution(struct s_problem &problem)
{
    bool status = true;

    PyRun_SimpleString(presolve);
    for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
    {
        if ( PyRun_FormatString("%s = cvx.Variable(n)",item->name) == -1 )
        {
            exception("unable to create CVX variable '%s'",item->name);
        }
    }


    if ( PyRun_FormatString("__objective__ = %s",problem.objective) == -1 )
    {
        exception("objective specification '%s' is invalid",problem.objective);
    }

    char buffer[1024];
    if ( PyRun_FormatString("__constraints__ = [%s]",constraints(buffer,sizeof(buffer)-1)>0?buffer:"") == -1 )
    {
        exception("constraints specification '[%s]' is invalid",buffer);
    }


    if ( PyRun_FormatString("__problem__ = cvx.Problem(__objective__,__constraints__)",get_name()) == -1 )
    {
        PyRun_SimpleString(on_failure);
        exception("problem construction failed");
    }

    if ( PyRun_SimpleString("__value__ = __problem__.solve()") == -1 )
    {
        PyRun_SimpleString(on_exception);
        exception("problem solve failed");
    }

    PyObject *value = PyDict_GetItemString(globals,"__value__");
    this->value = PyFloat_AsDouble(value);
    if ( ! isfinite(this->value) )
    {
        if ( this->value < 0 )
        {            
            PyRun_SimpleString(on_unbounded);
        }
        else
        {
            PyRun_SimpleString(on_infeasible);
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
        char buffer[65536] = "__result__ = {";
        int len = strlen(buffer);
        for ( VARIABLE *item = problem.variables ; item != NULL ; item = item->next )
        {
            len += snprintf(buffer+len,sizeof(buffer)-len-1,"'%s':%s.value.tolist() if not %s.value is None else []%s",
                item->name,item->name,item->name,item->next==NULL?"}":",");
        }
        // fprintf(stderr,"  Running '%s'...\n",buffer);
        PyRun_SimpleString(buffer);

        PyRun_SimpleString(postsolve);

        PyObject *result = PyDict_GetItemString(globals,"__result__");
        PyObject *key, *value;
        Py_ssize_t n = 0;
        while (  PyDict_Next(result, &n, &key, &value) )
        {
            const char *name = PyUnicode_AsUTF8AndSize(key,NULL);
            // fprintf(stderr,"%s = [\n",name);
            for ( Py_ssize_t n = 0 ; n < PyList_Size(value) ; n++ )
            {
                PyObject *data = PyList_GET_ITEM(value,n);
                // fprintf(stderr,"  %10.6f\n",PyFloat_AsDouble(data));
                Py_DECREF(data);
            }
            // fprintf(stderr,"  %s","]\n");
        }
        Py_DECREF(result);
        status = true;
    }
    Py_DECREF(value);

    return status;
}

