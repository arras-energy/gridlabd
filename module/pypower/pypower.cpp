// module/pypower/pypower.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#define DLMAIN

#include "pypower.h"

#include "Python.h"

bool enable_opf = false;
double base_MVA = 100.0;
int32 pypower_version = 2;
bool stop_on_failure = false;
int32 maximum_timestep = 0; // seconds; 0 = no max ts
typedef enum {
    PPSM_NR = 1, // Newton-Raphson
    PPSM_FDXB = 2, // Fast-decoupled XB method
    PPSM_FDBX = 3, // Fast-decoupled BX method
    PPSM_GS = 4, // Gauss-Seidel
} PYPOWERSOLVERMETHOD;
enumeration solver_method = PPSM_NR;
int32 maximum_iterations = 0; // default to pypower default for solver_method
double solution_tolerance = 0; // default to pypower default
double solver_update_resolution = 1e-8; 
bool save_case = false;
bool enforce_q_limits = false;
bool use_dc_powerflow = false;
typedef enum {
    PPSF_CSV = 0, // CSV files
    PPSF_JSON = 1, // JSON file
    PPSF_PY = 2, // PyPower case file
} PYPOWERSAVEFORMAT;
enumeration save_format = PPSF_CSV;
const char *save_formats[] = {"csv","json","py"};
double total_loss = 0;
double generation_shortfall = 0;

enum {
    SS_INIT = 0,
    SS_SUCCESS = 1,
    SS_FAILED = 2,
} solver_status;

char1024 controllers;
char1024 controllers_path;
PyObject *py_controllers;
PyObject *py_globals;
PyObject *py_precommit;
PyObject *py_sync;
PyObject *py_commit;

EXPORT CLASS *init(CALLBACKS *fntable, MODULE *module, int argc, char *argv[])
{
    if (set_callback(fntable)==NULL)
    {
        errno = EINVAL;
        return NULL;
    }

    INIT_MMF(pypower);

    new bus(module);
    new branch(module);
    new gen(module);
    new gencost(module);
    new geodata(module);
    new load(module);
    new powerplant(module);
    new powerline(module);
    new relay(module);
    new scada(module);
    new transformer(module);
    new weather(module);

    gl_global_create("pypower::version",
        PT_int32, &pypower_version, 
        PT_DESCRIPTION, "Version of pypower used",
        NULL);

    gl_global_create("pypower::solver_method",
        PT_enumeration, &solver_method,
        PT_KEYWORD, "GS", (enumeration)4,
        PT_KEYWORD, "FD_BX", (enumeration)3,
        PT_KEYWORD, "FD_XB", (enumeration)2,
        PT_KEYWORD, "NR", (enumeration)1,
        PT_DESCRIPTION, "PyPower solver method to use",
        NULL
        );

    gl_global_create("pypower::maximum_timestep",
        PT_int32, &maximum_timestep, 
        PT_DESCRIPTION, "Maximum timestep allowed between solutions",
        NULL);

    gl_global_create("pypower::baseMVA",
        PT_double, &base_MVA, 
        PT_UNITS, "MVA", 
        PT_DESCRIPTION, "Base MVA value",
        NULL);

    gl_global_create("pypower::enable_opf",
        PT_bool, &enable_opf, 
        PT_DESCRIPTION, "Flag to enable optimal powerflow (OPF) solver",
        NULL);

    gl_global_create("pypower::stop_on_failure",
        PT_bool, &stop_on_failure, 
        PT_DESCRIPTION, "Flag to stop simulation on solver failure",
        NULL);

    gl_global_create("pypower::save_case",
        PT_bool, &save_case, 
        PT_DESCRIPTION, "Flag to save pypower case data and results",
        NULL);

    gl_global_create("pypower::controllers_path",
        PT_char1024, &controllers_path, 
        PT_DESCRIPTION, "Path to find module containing controller functions",
        NULL);

    gl_global_create("pypower::controllers",
        PT_char1024, &controllers, 
        PT_DESCRIPTION, "Python module containing controller functions",
        NULL);

    gl_global_create("pypower::solver_update_resolution",
        PT_double, &solver_update_resolution,
        PT_DESCRIPTION, "Minimum difference before a value is considered changed",
        NULL);

    gl_global_create("pypower::maximum_iterations",
        PT_int32, &maximum_iterations,
        PT_DESCRIPTION, "Maximum iterations (0 defaults to pypower default for solver_method)",
        NULL);

    gl_global_create("pypower::solution_tolerance",
        PT_double, &solution_tolerance,
        PT_DESCRIPTION, "Solver convergence error tolerante (0 defaults to pypower default)",
        NULL);

    gl_global_create("pypower::solver_status",
        PT_enumeration, &solver_status,
        PT_KEYWORD, "INIT", (enumeration)SS_INIT,
        PT_KEYWORD, "SUCCESS", (enumeration)SS_SUCCESS,
        PT_KEYWORD, "FAILED", (enumeration)SS_FAILED,
        PT_DESCRIPTION, "Result of the last pypower solver run",
        NULL);

    gl_global_create("pypower::enforce_q_limits",
        PT_bool, &enforce_q_limits,
        PT_DESCRIPTION, "Enable enforcement of reactive power limits",
        NULL);

    gl_global_create("pypower::use_dc_powerflow",
        PT_bool, &use_dc_powerflow,
        PT_DESCRIPTION, "Enable use of DC powerflow solution",
        NULL);

    gl_global_create("pypower::save_format",
        PT_enumeration, &save_format,
        PT_KEYWORD, "CSV", (enumeration)PPSF_CSV,
        PT_KEYWORD, "JSON", (enumeration)PPSF_JSON,
        PT_KEYWORD, "PY", (enumeration)PPSF_PY,
        PT_DESCRIPTION, "Save case format",
        NULL);

    gl_global_create("pypower::total_loss",
        PT_double, &total_loss,
        PT_UNITS, "MW",
        PT_DESCRIPTION, "System-wide line losses",
        NULL);

    gl_global_create("pypower::generation_shortfall",
        PT_double, &generation_shortfall,
        PT_UNITS, "MW",
        PT_DESCRIPTION, "System-wide generation shortfall",
        NULL);

    // always return the first class registered
    return bus::oclass;
}

PyObject *solver = NULL;
PyObject *data = NULL;

size_t nbus = 0;
bus *buslist[MAXENT];
PyObject *busdata = NULL;

size_t nbranch = 0;
branch *branchlist[MAXENT];
PyObject *branchdata = NULL;

size_t ngen = 0;
gen *genlist[MAXENT];
PyObject *gendata = NULL;

size_t ngencost = 0;
gencost *gencostlist[MAXENT];
PyObject *gencostdata = NULL;

EXPORT bool on_init(void)
{
    // import controllers, if any
    if ( controllers[0] != '\0' )
    {
        if ( controllers_path[0] != '\0' )
        {
            char buffer[2000];
            snprintf(buffer,2000,"import sys\n"
               "sys.path.append('%s')\n", (const char *)controllers_path);
            PyRun_SimpleString(buffer);        
        }
        py_controllers = PyImport_ImportModule(controllers);
        if ( py_controllers == NULL )
        {
            if ( PyErr_Occurred() )
            {
                PyErr_Print();
            }
            else
            {  
                gl_error("unable to load controllers module '%s'",(const char*)controllers);
            }
            return false;
        }

        py_globals = PyModule_GetDict(py_controllers);
        if ( py_globals == NULL )
        {
            gl_error("unable to get globals in '%s'",(const char*)controllers);
            return false;
        }
        Py_INCREF(py_globals);

        PyObject *on_init = PyDict_GetItemString(py_globals,"on_init");
        if ( on_init )
        {
            if ( ! PyCallable_Check(on_init) )
            {
                gl_error("%s.on_init() is not callable",(const char*)controllers);
                Py_DECREF(on_init);
                return false;
            }
            PyObject *result = PyObject_CallNoArgs(on_init);
            if ( result == NULL )
            {
                if ( PyErr_Occurred() )
                {
                    PyErr_Print();
                }
                else
                {  
                    gl_error("%s.on_init() return None (expected bool)",(const char*)controllers);
                }
                return false;
            }
            if ( PyBool_Check(result) )
            {
                if ( ! PyObject_IsTrue(result) )
                {
                    gl_error("%s.on_init() failed (returned False)",(const char*)controllers);
                    Py_DECREF(result);
                    return false;
                }
            }
            else
            {
                    gl_error("%s.on_init() returned non-boolean value (expected True or False)",(const char*)controllers);
                    Py_DECREF(result);
                    return false;
            }
            Py_DECREF(result);
        }

        py_precommit = PyDict_GetItemString(py_globals,"on_precommit");
        if ( py_precommit )
        {
            if ( ! PyCallable_Check(py_precommit) )
            {
                gl_error("%s.on_precommit() is not callable",(const char*)controllers);
                return false;
            }
            Py_INCREF(py_precommit);
        }

        py_sync = PyDict_GetItemString(py_globals,"on_sync");
        if ( py_sync )
        {
            if ( ! PyCallable_Check(py_sync) )
            {
                gl_error("%s.on_sync() is not callable",(const char*)controllers);
                return false;
            }
            Py_INCREF(py_sync);
        }

        py_commit = PyDict_GetItemString(py_globals,"on_commit");
        if ( py_commit )
        {
            if ( ! PyCallable_Check(py_commit) )
            {
                gl_error("%s.on_commit() is not callable",(const char*)controllers);
                return false;
            }
            Py_INCREF(py_commit);
        }

    }

    // import pypower solver
    PyObject *module = PyImport_ImportModule("pypower_solver");
    if ( module == NULL )
    {
        if ( PyErr_Occurred() )
        {
            PyErr_Print();
        }
        else
        {  
            gl_error("unable to load pypower solver module (no info)");
        }
        return false;
    }
    solver = PyObject_GetAttrString(module,"solver");
    if ( solver == NULL )
    {
        gl_error("unable to find pypower solver call");
        return false;
    }

    // first time setup of arrays
    data = PyDict_New();
    PyDict_SetItemString(data,"version",PyLong_FromLong((long)pypower_version));
    PyDict_SetItemString(data,"baseMVA",PyFloat_FromDouble((double)base_MVA));

    busdata = PyList_New(nbus);
    for ( size_t n = 0 ; n < nbus ; n++ )
    {
        PyList_SET_ITEM(busdata,n,PyList_New(enable_opf?17:13));
    }
    PyDict_SetItemString(data,"bus",busdata);

    branchdata = PyList_New(nbranch);
    PyDict_SetItemString(data,"branch",branchdata);
    for ( size_t n = 0 ; n < nbranch ; n++ )
    {
        PyList_SET_ITEM(branchdata,n,PyList_New(13));
    }

    gendata = PyList_New(ngen);
    PyDict_SetItemString(data,"gen",gendata);
    for ( size_t n = 0 ; n < ngen ; n++ )
    {
        PyList_SET_ITEM(gendata,n,PyList_New(enable_opf?25:21));
    }

    if ( enable_opf )
    {
        gencostdata = PyList_New(ngencost); 
        PyDict_SetItemString(data,"gencost",gencostdata);
        for ( size_t n = 0; n < ngencost ; n++ )
        {
            PyList_SET_ITEM(gencostdata,n,PyList_New(4));
        }
    }

    // set options
    gld_global global_verbose("verbose");
    PyDict_SetItemString(data,"verbose",global_verbose.get_bool()?Py_True:Py_False);

    gld_global global_debug("debug");
    PyDict_SetItemString(data,"debug",global_debug.get_bool()?Py_True:Py_False);

    PyDict_SetItemString(data,"solver_method",PyLong_FromLong(solver_method));
    if ( maximum_iterations > 0 && solver_method > 0 && solver_method <= 4 )
    {
        const char *name[] = {
            "maximum_iterations_nr",
            "maximum_iterations_fd",
            "maximum_iterations_fd",
            "maximum_iterations_gs",
        };
        PyDict_SetItemString(data,name[solver_method-1],PyLong_FromLong(maximum_iterations));
    }
    if ( solution_tolerance > 0.0 )
    {
        PyDict_SetItemString(data,"solution_tolerance",PyFloat_FromDouble(solution_tolerance));
    }
    PyDict_SetItemString(data,"enforce_q_limits",enforce_q_limits?Py_True:Py_False);
    PyDict_SetItemString(data,"use_dc_powerflow",use_dc_powerflow?Py_True:Py_False);
    PyDict_SetItemString(data,"save_case",save_case?Py_True:Py_False);
    PyDict_SetItemString(data,"save_format",PyUnicode_FromString((const char*)save_formats[save_format]));
    char buffer[1025];
    if ( gl_global_getvar("modelname",buffer,sizeof(buffer)-1) )
    {
        *strrchr(buffer,'.')='\0';
        PyDict_SetItemString(data,"modelname",PyUnicode_FromString(buffer));
    }

    return true;
}

// conditional solver send/receive (only if value differs or is not set yet)
#define SEND(INDEX,NAME,FROM,TO) { PyObject *py = PyList_GetItem(pyobj,INDEX); \
    if ( py == NULL || fabs(obj->get_##NAME()-Py##TO##_As##FROM(py)) > solver_update_resolution ) { \
        PyObject *value = Py##TO##_From##FROM(obj->get_##NAME()); \
        if ( value == NULL ) { \
            gl_warning("pypower:on_*(t0=%lld): unable to create value " #NAME " for data item %d",t0,INDEX); \
        } \
        else { \
            PyList_SET_ITEM(pyobj,INDEX,value); \
            Py_XDECREF(py); \
            n_changes++; \
}}}

#define RECV(NAME,INDEX,FROM,TO) { PyObject *py = PyList_GET_ITEM(pyobj,INDEX);\
    if ( fabs(obj->get_##NAME()-Py##FROM##_As##TO(py)) > solver_update_resolution ) { \
        n_changes++; \
        obj->set_##NAME(Py##FROM##_As##TO(py)); \
    }}

#define SENDX(INDEX,NAME,FROM,TO) { PyObject *py = PyList_GetItem(pyobj,INDEX); \
    if ( py == NULL || fabs(obj->get_##NAME()-Py##TO##_As##FROM(py)) > solver_update_resolution ) { \
        PyObject *value = Py##TO##_From##FROM(obj->get_##NAME()); \
        if ( value == NULL ) { \
            gl_warning("pypower:on_*(t0=%lld): unable to create value " #NAME " for data item %d",t0,INDEX); \
        } \
        else { \
            PyList_SET_ITEM(pyobj,INDEX,value); \
            Py_XDECREF(py); \
}}}

#define RECVX(NAME,INDEX,FROM,TO) { PyObject *py = PyList_GET_ITEM(pyobj,INDEX);\
    if ( fabs(obj->get_##NAME()-Py##FROM##_As##TO(py)) > solver_update_resolution ) { \
        obj->set_##NAME(Py##FROM##_As##TO(py)); \
    }}

EXPORT TIMESTAMP on_precommit(TIMESTAMP t0)
{
    // not a pypower model
    if ( nbus == 0 || nbranch == 0 )
    {
        return TS_NEVER;
    }

    // send values out to solver
    for ( size_t n = 0 ; n < nbus ; n++ )
    {
        bus *obj = buslist[n];
        PyObject *pyobj = PyList_GetItem(busdata,n);
        SENDX(0,bus_i,Double,Float)
        SENDX(1,type,Long,Long)
        SENDX(2,Pd,Double,Float)
        SENDX(3,Qd,Double,Float)
        SENDX(4,Gs,Double,Float)
        SENDX(5,Bs,Double,Float)
        SENDX(6,area,Long,Long)
        SENDX(7,Vm,Double,Float)
        SENDX(8,Va,Double,Float)
        SENDX(9,baseKV,Double,Float)
        SENDX(10,zone,Long,Long)
        SENDX(11,Vmax,Double,Float)
        SENDX(12,Vmin,Double,Float)
        if ( enable_opf )
        {
            SENDX(13,lam_P,Double,Float)
            SENDX(14,lam_Q,Double,Float)
            SENDX(15,mu_Vmax,Double,Float)
            SENDX(16,mu_Vmin,Double,Float)
        }
    }
    for ( size_t n = 0 ; n < nbranch ; n++ )
    {
        branch *obj = branchlist[n];
        PyObject *pyobj = PyList_GetItem(branchdata,n);
        SENDX(0,fbus,Long,Long)
        SENDX(1,tbus,Long,Long)
        SENDX(2,r,Double,Float)
        SENDX(3,x,Double,Float)
        SENDX(4,b,Double,Float)
        SENDX(5,rateA,Double,Float)
        SENDX(6,rateB,Double,Float)
        SENDX(7,rateC,Double,Float)
        SENDX(8,ratio,Double,Float)
        SENDX(9,angle,Double,Float)
        SENDX(10,status,Long,Long)
        SENDX(11,angmin,Double,Float)
        SENDX(12,angmax,Double,Float)

    }
    for ( size_t n = 0 ; n < ngen ; n++ )
    {
        gen *obj = genlist[n];
        PyObject *pyobj = PyList_GetItem(gendata,n);
        SENDX(0,bus,Long,Long)
        SENDX(1,Pg,Double,Float)
        SENDX(2,Qg,Double,Float)
        SENDX(3,Qmax,Double,Float)
        SENDX(4,Qmin,Double,Float)
        SENDX(5,Vg,Double,Float)
        SENDX(6,mBase,Double,Float)
        SENDX(7,status,Long,Long)
        SENDX(8,Pmax,Double,Float)
        SENDX(9,Pmin,Double,Float)
        SENDX(10,Pc1,Double,Float)
        SENDX(11,Pc2,Double,Float)
        SENDX(12,Qc1min,Double,Float)
        SENDX(13,Qc1max,Double,Float)
        SENDX(14,Qc2min,Double,Float)
        SENDX(15,Qc2max,Double,Float)
        SENDX(16,ramp_agc,Double,Float)
        SENDX(17,ramp_10,Double,Float)
        SENDX(18,ramp_30,Double,Float)
        SENDX(19,ramp_q,Double,Float)
        SENDX(20,apf,Double,Float)
        if ( enable_opf )
        {
            SENDX(21,mu_Pmax,Double,Float)
            SENDX(22,mu_Pmin,Double,Float)
            SENDX(23,mu_Qmax,Double,Float)
            SENDX(24,mu_Qmin,Double,Float)
        }
    }
    if ( gencostdata )
    {
        for ( size_t n = 0 ; n < ngencost ; n++ )
        {
            gencost *obj = gencostlist[n];
            PyObject *pyobj = PyList_GetItem(gencostdata,n);
            SENDX(0,model,Long,Long)
            SENDX(1,startup,Double,Float)
            SENDX(2,shutdown,Double,Float)
            PyObject *py = PyList_GetItem(pyobj,3);
            if ( py == NULL || strcmp((const char*)PyUnicode_DATA(py),obj->get_costs())!=0 )
            {
                Py_XDECREF(py);
                PyList_SET_ITEM(pyobj,3,PyUnicode_FromString(obj->get_costs()));
            }
        }
    }

    // run controller on_precommit, if any
    TIMESTAMP t1 = TS_NEVER;
    if ( py_precommit )
    {
        PyDict_SetItemString(data,"t",PyLong_FromLong(t0));        
        PyErr_Clear();
        PyObject *ts = PyObject_CallOneArg(py_precommit,data);
        if ( PyErr_Occurred() )
        {
            PyErr_Print();
            return TS_INVALID;
        }
        if ( ts == NULL || ! PyLong_Check(ts) )
        {
            gl_error("%s.on_precommit(data) returned value that is not a valid timestamp",(const char*)controllers);
            Py_XDECREF(ts);
            return TS_INVALID;
        }
        t1 = PyLong_AsLong(ts);
        Py_DECREF(ts);
        if ( t1 < 0 )
        {
            t1 = TS_NEVER;
        }
        else if ( t1 == 0 && stop_on_failure )
        {
            gl_error("%s.on_precommit(data) halted the simulation",(const char*)controllers);
            return TS_INVALID;
        }
        else if ( t1 < t0 )
        {
            gl_error("%s.on_precommit(data) returned a timestamp earlier than precommit time t0=%lld",(const char*)controllers,t0);
            return TS_INVALID;
        }
    }

    TIMESTAMP t2 = maximum_timestep > 0 ? t0+maximum_timestep : TS_NEVER;
    return (TIMESTAMP)min((unsigned long long)t1,(unsigned long long)t2);
}

EXPORT TIMESTAMP on_sync(TIMESTAMP t0)
{
    // not a pypower model
    if ( nbus == 0 || nbranch == 0 )
    {
        return TS_NEVER;
    }

    int n_changes = 0;

    // send values out to solver
    for ( size_t n = 0 ; n < nbus ; n++ )
    {
        bus *obj = buslist[n];
        PyObject *pyobj = PyList_GetItem(busdata,n);
        SEND(0,bus_i,Double,Float)
        SEND(1,type,Long,Long)
        SEND(2,Pd,Double,Float)
        SEND(3,Qd,Double,Float)
        SEND(4,Gs,Double,Float)
        SEND(5,Bs,Double,Float)
        SEND(6,area,Long,Long)
        SEND(7,Vm,Double,Float)
        SEND(8,Va,Double,Float)
        SEND(9,baseKV,Double,Float)
        SEND(10,zone,Long,Long)
        SEND(11,Vmax,Double,Float)
        SEND(12,Vmin,Double,Float)
        if ( enable_opf )
        {
            SEND(13,lam_P,Double,Float)
            SEND(14,lam_Q,Double,Float)
            SEND(15,mu_Vmax,Double,Float)
            SEND(16,mu_Vmin,Double,Float)
        }
    }
    for ( size_t n = 0 ; n < nbranch ; n++ )
    {
        branch *obj = branchlist[n];
        PyObject *pyobj = PyList_GetItem(branchdata,n);
        SEND(0,fbus,Long,Long)
        SEND(1,tbus,Long,Long)
        SEND(2,r,Double,Float)
        SEND(3,x,Double,Float)
        SEND(4,b,Double,Float)
        SEND(5,rateA,Double,Float)
        SEND(6,rateB,Double,Float)
        SEND(7,rateC,Double,Float)
        SEND(8,ratio,Double,Float)
        SEND(9,angle,Double,Float)
        SEND(10,status,Long,Long)
        SEND(11,angmin,Double,Float)
        SEND(12,angmax,Double,Float)

    }
    for ( size_t n = 0 ; n < ngen ; n++ )
    {
        gen *obj = genlist[n];
        PyObject *pyobj = PyList_GetItem(gendata,n);
        SEND(0,bus,Long,Long)
        SEND(1,Pg,Double,Float)
        SEND(2,Qg,Double,Float)
        SEND(3,Qmax,Double,Float)
        SEND(4,Qmin,Double,Float)
        SEND(5,Vg,Double,Float)
        SEND(6,mBase,Double,Float)
        SEND(7,status,Long,Long)
        SEND(8,Pmax,Double,Float)
        SEND(9,Pmin,Double,Float)
        SEND(10,Pc1,Double,Float)
        SEND(11,Pc2,Double,Float)
        SEND(12,Qc1min,Double,Float)
        SEND(13,Qc1max,Double,Float)
        SEND(14,Qc2min,Double,Float)
        SEND(15,Qc2max,Double,Float)
        SEND(16,ramp_agc,Double,Float)
        SEND(17,ramp_10,Double,Float)
        SEND(18,ramp_30,Double,Float)
        SEND(19,ramp_q,Double,Float)
        SEND(20,apf,Double,Float)
        if ( enable_opf )
        {
            SEND(21,mu_Pmax,Double,Float)
            SEND(22,mu_Pmin,Double,Float)
            SEND(23,mu_Qmax,Double,Float)
            SEND(24,mu_Qmin,Double,Float)
        }
    }
    if ( gencostdata )
    {
        for ( size_t n = 0 ; n < ngencost ; n++ )
        {
            gencost *obj = gencostlist[n];
            PyObject *pyobj = PyList_GetItem(gencostdata,n);
            SEND(0,model,Long,Long)
            SEND(1,startup,Double,Float)
            SEND(2,shutdown,Double,Float)
            PyObject *py = PyList_GetItem(pyobj,3);
            if ( py == NULL || strcmp((const char*)PyUnicode_DATA(py),obj->get_costs())!=0 )
            {
                Py_XDECREF(py);
                PyList_SET_ITEM(pyobj,3,PyUnicode_FromString(obj->get_costs()));
            }
        }
    }

    // run controller on_sync, if any
    TIMESTAMP t1 = TS_NEVER;
    if ( py_sync )
    {
        PyDict_SetItemString(data,"t",PyLong_FromLong(t0));        
        PyErr_Clear();
        PyObject *ts = PyObject_CallOneArg(py_sync,data);
        if ( PyErr_Occurred() )
        {
            PyErr_Print();
            return TS_INVALID;
        }
        if ( ts == NULL || ! PyLong_Check(ts) )
        {
            gl_error("%s.on_sync(data) returned value that is not a valid timestamp",(const char*)controllers);
            Py_XDECREF(ts);
            return TS_INVALID;
        }
        t1 = PyLong_AsLong(ts);
        Py_DECREF(ts);
        if ( t1 < 0 )
        {
            t1 = TS_NEVER;
        }
        else if ( t1 == 0 && stop_on_failure )
        {
            gl_error("%s.on_sync(data) halted the simulation",(const char*)controllers);
            return TS_INVALID;
        }
        else if ( t1 < t0 )
        {
            gl_error("%s.on_sync(data) returned a timestamp earlier than sync time t0=%lld",(const char*)controllers,t0);
            return TS_INVALID;
        }
    }

    // run solver
    static PyObject *result = NULL;
    if ( result == NULL || n_changes > 0 )
    {
        // run pypower solver
        if ( result != data )
        {
            Py_XDECREF(result);
        }
        PyErr_Clear();
        result = PyObject_CallOneArg(solver,data);

        // receive results (if new)
        if ( result != NULL )
        {
            if ( result == Py_False )
            {
                if ( stop_on_failure )
                {
                    gl_error("pypower solver failed");
                    solver_status = SS_FAILED;
                    return TS_INVALID;
                }
                else
                {
                    gl_warning("pypower solver failed");
                    solver_status = SS_FAILED;
                    return TS_NEVER;
                }
            }
            else if ( ! PyDict_Check(result) )
            {
                gl_error("pypower solver returned invalid result type (not a dict)");
                fprintf(stderr," result = %s\n", PyBytes_AS_STRING(PyUnicode_AsEncodedString(PyObject_Repr(result),"utf-8","~E~")));
                solver_status = SS_FAILED;
                return TS_INVALID;
            }

            // copy values back from solver
            n_changes = 0;
            PyObject *busdata = PyDict_GetItemString(result,"bus");
            if ( nbus > 0 && busdata == NULL )
            {
                gl_error("pypower solver did not return any bus data");
                solver_status = SS_FAILED;
                return TS_INVALID;
            }
            for ( size_t n = 0 ; n < nbus ; n++ )
            {
                bus *obj = buslist[n];
                PyObject *pyobj = PyList_GetItem(busdata,n);
                RECV(Vm,7,Float,Double)
                RECV(Va,8,Float,Double)

                if ( enable_opf )
                {
                    RECV(lam_P,13,Float,Double)
                    RECV(lam_Q,14,Float,Double)
                    RECV(mu_Vmax,15,Float,Double)
                    RECV(mu_Vmin,16,Float,Double)
                }
                obj->V.SetPolar(obj->get_Vm(),obj->get_Va());
            }

            for ( size_t n = 0 ; n < nbranch ; n++ )
            {
                branch *line = branchlist[n];
                size_t fbus_id = line->get_fbus()-1;
                size_t tbus_id = line->get_tbus()-1;
                if ( fbus_id < 0 || fbus_id >= nbus )
                {
                    gl_warning("pypower::on_sync(): from bus %d on branch %d is not valid",fbus_id,n);
                }
                else if ( tbus_id < 0 || tbus_id >= nbus )
                {
                    gl_warning("pypower::on_sync(): to bus %d on branch %d is not valid",tbus_id,n);
                }
                else
                {
                    complex Z(line->get_r(),line->get_x());
                    bus *fbus = buslist[fbus_id];
                    bus *tbus = buslist[tbus_id];
                    complex DV = fbus->V - tbus->V;
                    complex current = DV / Z;
                    line->set_current(current*base_MVA);
                    double loss = (DV * ~current).Mag() / base_MVA;
                    line->set_loss(loss);
                    total_loss += loss;
                }
            }

            PyObject *gendata = PyDict_GetItemString(result,"gen");
            if ( ngencost > 0 && gendata == NULL )
            {
                gl_error("pypower solver did not return any gen data");
                solver_status = SS_FAILED;
                return TS_INVALID;
            }
            generation_shortfall = 0;
            for ( size_t n = 0 ; n < ngen ; n++ )
            {
                gen *obj = genlist[n];
                PyObject *pyobj = PyList_GetItem(gendata,n);
                RECV(Pg,1,Float,Double)
                RECV(Qg,2,Float,Double)
                RECV(apf,20,Float,Double)
                if ( enable_opf )
                {
                    RECV(mu_Pmax,21,Float,Double)
                    RECV(mu_Pmin,22,Float,Double)
                    RECV(mu_Qmax,23,Float,Double)
                    RECV(mu_Qmin,24,Float,Double)
                }
                generation_shortfall += max(obj->get_Pg() - obj->get_Pmax(),0.0);
            }
        }
    }

    PyErr_Clear();
    if ( result == NULL && stop_on_failure )
    {
        gl_warning("pypower solver failed");
        solver_status = SS_FAILED;
        return TS_INVALID;
    }
    else
    { 
        if ( ! result )
        {
            gl_warning("pypower solver failed");
            solver_status = SS_FAILED;
        }
        else
        {
            solver_status = SS_SUCCESS;
        }
        if ( n_changes > 0 )
        {
            return t0;
        }
        TIMESTAMP t2 = maximum_timestep > 0 ? t0+maximum_timestep : TS_NEVER;
        return (TIMESTAMP)min((unsigned long long)t1,(unsigned long long)t2);

    }
}

EXPORT int on_commit(TIMESTAMP t0)
{
    // not a pypower model
    if ( nbus == 0 || nbranch == 0 )
    {
        return 1;
    }

    // send values out to solver
    for ( size_t n = 0 ; n < nbus ; n++ )
    {
        bus *obj = buslist[n];
        PyObject *pyobj = PyList_GetItem(busdata,n);
        SENDX(0,bus_i,Double,Float)
        SENDX(1,type,Long,Long)
        SENDX(2,Pd,Double,Float)
        SENDX(3,Qd,Double,Float)
        SENDX(4,Gs,Double,Float)
        SENDX(5,Bs,Double,Float)
        SENDX(6,area,Long,Long)
        SENDX(7,Vm,Double,Float)
        SENDX(8,Va,Double,Float)
        SENDX(9,baseKV,Double,Float)
        SENDX(10,zone,Long,Long)
        SENDX(11,Vmax,Double,Float)
        SENDX(12,Vmin,Double,Float)
        if ( enable_opf )
        {
            SENDX(13,lam_P,Double,Float)
            SENDX(14,lam_Q,Double,Float)
            SENDX(15,mu_Vmax,Double,Float)
            SENDX(16,mu_Vmin,Double,Float)
        }
    }
    for ( size_t n = 0 ; n < nbranch ; n++ )
    {
        branch *obj = branchlist[n];
        PyObject *pyobj = PyList_GetItem(branchdata,n);
        SENDX(0,fbus,Long,Long)
        SENDX(1,tbus,Long,Long)
        SENDX(2,r,Double,Float)
        SENDX(3,x,Double,Float)
        SENDX(4,b,Double,Float)
        SENDX(5,rateA,Double,Float)
        SENDX(6,rateB,Double,Float)
        SENDX(7,rateC,Double,Float)
        SENDX(8,ratio,Double,Float)
        SENDX(9,angle,Double,Float)
        SENDX(10,status,Long,Long)
        SENDX(11,angmin,Double,Float)
        SENDX(12,angmax,Double,Float)

    }
    for ( size_t n = 0 ; n < ngen ; n++ )
    {
        gen *obj = genlist[n];
        PyObject *pyobj = PyList_GetItem(gendata,n);
        SENDX(0,bus,Long,Long)
        SENDX(1,Pg,Double,Float)
        SENDX(2,Qg,Double,Float)
        SENDX(3,Qmax,Double,Float)
        SENDX(4,Qmin,Double,Float)
        SENDX(5,Vg,Double,Float)
        SENDX(6,mBase,Double,Float)
        SENDX(7,status,Long,Long)
        SENDX(8,Pmax,Double,Float)
        SENDX(9,Pmin,Double,Float)
        SENDX(10,Pc1,Double,Float)
        SENDX(11,Pc2,Double,Float)
        SENDX(12,Qc1min,Double,Float)
        SENDX(13,Qc1max,Double,Float)
        SENDX(14,Qc2min,Double,Float)
        SENDX(15,Qc2max,Double,Float)
        SENDX(16,ramp_agc,Double,Float)
        SENDX(17,ramp_10,Double,Float)
        SENDX(18,ramp_30,Double,Float)
        SENDX(19,ramp_q,Double,Float)
        SENDX(20,apf,Double,Float)
        if ( enable_opf )
        {
            SENDX(21,mu_Pmax,Double,Float)
            SENDX(22,mu_Pmin,Double,Float)
            SENDX(23,mu_Qmax,Double,Float)
            SENDX(24,mu_Qmin,Double,Float)
        }
    }
    if ( gencostdata )
    {
        for ( size_t n = 0 ; n < ngencost ; n++ )
        {
            gencost *obj = gencostlist[n];
            PyObject *pyobj = PyList_GetItem(gencostdata,n);
            SENDX(0,model,Long,Long)
            SENDX(1,startup,Double,Float)
            SENDX(2,shutdown,Double,Float)
            PyObject *py = PyList_GetItem(pyobj,3);
            if ( py == NULL || strcmp((const char*)PyUnicode_DATA(py),obj->get_costs())!=0 )
            {
                Py_XDECREF(py);
                PyList_SET_ITEM(pyobj,3,PyUnicode_FromString(obj->get_costs()));
            }
        }
    }

    // run controller on_commit, if any
    if ( py_commit )
    {
        PyDict_SetItemString(data,"t",PyLong_FromLong(t0));        
        PyErr_Clear();
        PyObject *ts = PyObject_CallOneArg(py_commit,data);
        if ( PyErr_Occurred() )
        {
            PyErr_Print();
            return 0;
        }
        Py_DECREF(ts);
    }

    return 1;
}

EXPORT int do_kill(void*)
{
    // if global memory needs to be released, this is a good time to do it
    Py_XDECREF(busdata);
    Py_XDECREF(branchdata);
    Py_XDECREF(gendata);
    Py_XDECREF(gencostdata);

    return 0;
}

EXPORT int check(){
    // if any assert objects have bad filenames, they'll fail on init()
    return 0;
}
