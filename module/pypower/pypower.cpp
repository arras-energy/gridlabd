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

    gl_global_create("pypower::version",
        PT_int32, &pypower_version, 
        PT_DESCRIPTION, "Version of pypower used",
        NULL);

    gl_global_create("pypower::solver_method",
        PT_enumeration, &solver_method,
        PT_KEYWORD, "NR", (enumeration)1,
        PT_KEYWORD, "FD_XB", (enumeration)2,
        PT_KEYWORD, "FD_BX", (enumeration)3,
        PT_KEYWORD, "GS", (enumeration)4,
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
    // import solver
    PyObject *module = PyImport_ImportModule("pypower_solver");
    if ( module == NULL )
    {
        gl_error("unable to load pypower solver module");
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
        PyList_SetItem(busdata,n,PyList_New(enable_opf?17:13));
    }
    PyDict_SetItemString(data,"bus",busdata);

    branchdata = PyList_New(nbranch);
    PyDict_SetItemString(data,"branch",branchdata);
    for ( size_t n = 0 ; n < nbranch ; n++ )
    {
        PyList_SetItem(branchdata,n,PyList_New(13));
    }

    gendata = PyList_New(ngen);
    PyDict_SetItemString(data,"gen",gendata);
    for ( size_t n = 0 ; n < ngen ; n++ )
    {
        PyList_SetItem(gendata,n,PyList_New(enable_opf?25:21));
    }

    if ( enable_opf )
    {
        gencostdata = PyList_New(ngencost); 
        PyDict_SetItemString(data,"gencost",gencostdata);
        for ( size_t n = 0; n < ngencost ; n++ )
        {
            PyList_SetItem(gencostdata,n,PyList_New(4));
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
#define SEND(INDEX,NAME,FROM,TO) if ( PyList_GET_ITEM(pyobj,INDEX) == NULL || Py##TO##_As##FROM(PyList_GET_ITEM(pyobj,INDEX)) ) PyList_SetItem(pyobj,INDEX,Py##TO##_From##FROM(obj->get_##NAME()));

EXPORT TIMESTAMP on_sync(TIMESTAMP t0)
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
        SEND(0,bus_i,Double,Float)
        SEND(1,type,Long,Long)
        // SEND(2,Pd,Double,Float)
        // SEND(3,Qd,Double,Float)
        PyList_SetItem(pyobj,2,PyFloat_FromDouble(obj->get_total_load().Re()));
        PyList_SetItem(pyobj,3,PyFloat_FromDouble(obj->get_total_load().Im()));
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
            if ( PyList_GET_ITEM(pyobj,3) == NULL || strcmp((const char*)PyUnicode_DATA(PyList_GET_ITEM(pyobj,3)),obj->get_costs())!=0 )
            {
                PyList_SetItem(pyobj,3,PyUnicode_FromString(obj->get_costs()));
            }
        }
    }

    // run solver
    PyErr_Clear();
    PyObject *result = PyObject_CallOneArg(solver,data) ;

    // receive results
    if ( result )
    {
        if ( ! PyDict_Check(result) )
        {
            gl_error("pypower solver returned invalid result type (not a dict)");
            return TS_INVALID;
        }

        // copy values back from solver
        PyObject *busdata = PyDict_GetItemString(result,"bus");
        for ( size_t n = 0 ; n < nbus ; n++ )
        {
            bus *obj = buslist[n];
            PyObject *pyobj = PyList_GetItem(busdata,n);
            obj->set_Vm(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,7)));
            obj->set_Va(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,8)));

            if ( enable_opf )
            {
                obj->set_lam_P(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,13)));
                obj->set_lam_Q(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,14)));
                obj->set_mu_Vmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,15)));
                obj->set_mu_Vmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,16)));
            }
        }

        PyObject *gendata = PyDict_GetItemString(result,"gen");
        for ( size_t n = 0 ; n < ngen ; n++ )
        {
            gen *obj = genlist[n];
            PyObject *pyobj = PyList_GetItem(gendata,n);
            obj->set_Pg(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,1)));
            obj->set_Qg(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,2)));
            obj->set_apf(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,20)));
            if ( enable_opf )
            {
                obj->set_mu_Pmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,21)));
                obj->set_mu_Pmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,22)));
                obj->set_mu_Qmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,23)));
                obj->set_mu_Qmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,24)));
            }
        }
    }
    Py_XDECREF(result);
    PyErr_Clear();

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
