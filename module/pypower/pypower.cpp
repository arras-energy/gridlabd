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
enumeration solver_method = 1;
bool save_case = false;
char1024 controllers;
char1024 controllers_path;
PyObject *py_controllers;
PyObject *py_globals;

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
    new load(module);
    new powerplant(module);
    new powerline(module);

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
                Py_DECREF(on_init);
                return false;
            }
            if ( PyBool_Check(result) )
            {
                if ( ! PyObject_IsTrue(result) )
                {
                    gl_error("%s.on_init() failed (returned False)",(const char*)controllers);
                    Py_DECREF(on_init);
                    Py_DECREF(result);
                    return false;
                }
            }
            else
            {
                    gl_error("%s.on_init() returned non-boolean value (expected True or False)",(const char*)controllers);
                    Py_DECREF(on_init);
                    Py_DECREF(result);
                    return false;
            }

            Py_DECREF(on_init);
            Py_DECREF(result);
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
    PyDict_SetItemString(data,"verbose",global_verbose=="TRUE"?Py_True:Py_False);

    gld_global global_debug("debug");
    PyDict_SetItemString(data,"debug",global_debug=="TRUE"?Py_True:Py_False);

    PyDict_SetItemString(data,"solver_method",PyLong_FromLong(solver_method));
    PyDict_SetItemString(data,"save_case",save_case?Py_True:Py_False);

    return true;
}

// conditional send (only if value differs or is not set yet)
#define SEND(INDEX,NAME,FROM,TO) { PyObject *py = PyList_GetItem(pyobj,INDEX); \
    if ( py == NULL || obj->get_##NAME() != Py##TO##_As##FROM(py) ) { \
        PyObject *value = Py##TO##_From##FROM(obj->get_##NAME()); \
        if ( value == NULL ) { \
            gl_warning("pypower:on_sync(t0=%lld): unable to create value " #NAME " for data item %d",t0,INDEX); \
        } \
        else { \
            PyList_SET_ITEM(pyobj,INDEX,value); \
            Py_XDECREF(py); \
            n_changes++; \
}}}

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

    // run solver
    PyErr_Clear();
    static PyObject *result = NULL;
    if ( result == NULL || n_changes > 0 )
    {
        if ( result != data )
        {
            Py_XDECREF(result);
        }
        result = PyObject_CallOneArg(solver,data);

        // receive results (if new)
        if ( result != NULL && result != data )
        {
            if ( ! PyDict_Check(result) )
            {
                gl_error("pypower solver returned invalid result type (not a dict)");
                return TS_INVALID;
            }

#define RECV(NAME,INDEX,FROM,TO) { PyObject *py = PyList_GET_ITEM(pyobj,INDEX);\
    if ( obj->get_##NAME() != Py##FROM##_As##TO(py) ) { \
        n_changes++; \
        obj->set_##NAME(Py##FROM##_As##TO(py)); \
    }}

            // copy values back from solver
            n_changes = 0;
            PyObject *busdata = PyDict_GetItemString(result,"bus");
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
            }

            PyObject *gendata = PyDict_GetItemString(result,"gen");
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
            }
        }
        PyErr_Clear();
    }

    if ( result == NULL && stop_on_failure )
    {
        gl_warning("pypower solver failed");
        return TS_INVALID;
    }
    else
    { 
        if ( ! result )
        {
            gl_warning("pypower solver failed");
        }
        if ( n_changes > 0 )
        {
            return t0;
        }
        return maximum_timestep > 0 ? t0+maximum_timestep : TS_NEVER;

    }
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
