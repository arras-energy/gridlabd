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
    // TODO: add support for OPF
    // new gencost(module);

    gl_global_create("pypower::version",
        PT_int32, &pypower_version, 
        PT_DESCRIPTION, "Version of pypower used",
        NULL);

    gl_global_create("pypower::solver_method",
        PT_enumeration, &solver_method,
        PT_KEYWORD, "NR", (enumeration)1,
        PT_KEYWORD, "FD-XB", (enumeration)1,
        PT_KEYWORD, "FD-BX", (enumeration)1,
        PT_KEYWORD, "GS", (enumeration)1,
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

    // TODO: add support for OPF
    // gl_global_create("pypower::enable_opf",
    //     PT_bool, &enable_opf, 
    //     PT_DESCRIPTION, "Flag to enable optimal powerflow (OPF) solver",
    //     NULL);

    gl_global_create("pypower::stop_on_failure",
        PT_bool, &stop_on_failure, 
        PT_DESCRIPTION, "Flag to stop simulation on solver failure",
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
        // TODO: required for OPF solution
        throw "OPF not supported yet";
        // gencostdata = PyList_New(7); 
        // PyDict_SetItemString(data,"gencost",gencostdata);
    }

    return true;
}

EXPORT TIMESTAMP on_sync(TIMESTAMP t0)
{

    // copy values out to solver
    for ( size_t n = 0 ; n < nbus ; n++ )
    {
        bus *obj = buslist[n];
        PyObject *pyobj = PyList_GetItem(busdata,n);
        PyList_SetItem(pyobj,0,PyLong_FromLong(obj->get_bus_i()));
        PyList_SetItem(pyobj,1,PyLong_FromLong(obj->get_type()));
        PyList_SetItem(pyobj,2,PyFloat_FromDouble(obj->get_Pd()));
        PyList_SetItem(pyobj,3,PyFloat_FromDouble(obj->get_Qd()));
        PyList_SetItem(pyobj,4,PyFloat_FromDouble(obj->get_Gs()));
        PyList_SetItem(pyobj,5,PyFloat_FromDouble(obj->get_Bs()));
        PyList_SetItem(pyobj,6,PyLong_FromLong(obj->get_area()));
        PyList_SetItem(pyobj,7,PyFloat_FromDouble(obj->get_Vm()));
        PyList_SetItem(pyobj,8,PyFloat_FromDouble(obj->get_Va()));
        PyList_SetItem(pyobj,9,PyFloat_FromDouble(obj->get_baseKV()));
        PyList_SetItem(pyobj,10,PyLong_FromLong(obj->get_zone()));
        PyList_SetItem(pyobj,11,PyFloat_FromDouble(obj->get_Vmax()));
        PyList_SetItem(pyobj,12,PyFloat_FromDouble(obj->get_Vmin()));
        if ( enable_opf )
        {
            PyList_SetItem(pyobj,13,PyFloat_FromDouble(obj->get_lam_P()));
            PyList_SetItem(pyobj,14,PyFloat_FromDouble(obj->get_lam_Q()));
            PyList_SetItem(pyobj,15,PyFloat_FromDouble(obj->get_mu_Vmax()));
            PyList_SetItem(pyobj,16,PyFloat_FromDouble(obj->get_mu_Vmin()));
        }
    }
    for ( size_t n = 0 ; n < nbranch ; n++ )
    {
        branch *obj = branchlist[n];
        PyObject *pyobj = PyList_GetItem(branchdata,n);
        PyList_SetItem(pyobj,0,PyLong_FromLong(obj->get_fbus()));
        PyList_SetItem(pyobj,1,PyLong_FromLong(obj->get_tbus()));
        PyList_SetItem(pyobj,2,PyFloat_FromDouble(obj->get_r()));
        PyList_SetItem(pyobj,3,PyFloat_FromDouble(obj->get_x()));
        PyList_SetItem(pyobj,4,PyFloat_FromDouble(obj->get_b()));
        PyList_SetItem(pyobj,5,PyFloat_FromDouble(obj->get_rateA()));
        PyList_SetItem(pyobj,6,PyFloat_FromDouble(obj->get_rateB()));
        PyList_SetItem(pyobj,7,PyFloat_FromDouble(obj->get_rateC()));
        PyList_SetItem(pyobj,8,PyFloat_FromDouble(obj->get_ratio()));
        PyList_SetItem(pyobj,9,PyFloat_FromDouble(obj->get_angle()));
        PyList_SetItem(pyobj,10,PyLong_FromLong(obj->get_status()));
        PyList_SetItem(pyobj,11,PyFloat_FromDouble(obj->get_angmin()));
        PyList_SetItem(pyobj,12,PyFloat_FromDouble(obj->get_angmax()));

    }
    for ( size_t n = 0 ; n < ngen ; n++ )
    {
        gen *obj = genlist[n];
        PyObject *pyobj = PyList_GetItem(gendata,n);
        PyList_SetItem(pyobj,0,PyLong_FromLong(obj->get_bus()));
        PyList_SetItem(pyobj,1,PyFloat_FromDouble(obj->get_Pg()));
        PyList_SetItem(pyobj,2,PyFloat_FromDouble(obj->get_Qg()));
        PyList_SetItem(pyobj,3,PyFloat_FromDouble(obj->get_Qmax()));
        PyList_SetItem(pyobj,4,PyFloat_FromDouble(obj->get_Qmin()));
        PyList_SetItem(pyobj,5,PyFloat_FromDouble(obj->get_Vg()));
        PyList_SetItem(pyobj,6,PyFloat_FromDouble(obj->get_mBase()));
        PyList_SetItem(pyobj,7,PyLong_FromLong(obj->get_status()));
        PyList_SetItem(pyobj,8,PyFloat_FromDouble(obj->get_Pmax()));
        PyList_SetItem(pyobj,9,PyFloat_FromDouble(obj->get_Pmin()));
        PyList_SetItem(pyobj,10,PyFloat_FromDouble(obj->get_Pc1()));
        PyList_SetItem(pyobj,11,PyFloat_FromDouble(obj->get_Pc2()));
        PyList_SetItem(pyobj,12,PyFloat_FromDouble(obj->get_Qc1min()));
        PyList_SetItem(pyobj,13,PyFloat_FromDouble(obj->get_Qc1max()));
        PyList_SetItem(pyobj,14,PyFloat_FromDouble(obj->get_Qc2min()));
        PyList_SetItem(pyobj,15,PyFloat_FromDouble(obj->get_Qc2max()));
        PyList_SetItem(pyobj,16,PyFloat_FromDouble(obj->get_ramp_agc()));
        PyList_SetItem(pyobj,17,PyFloat_FromDouble(obj->get_ramp_10()));
        PyList_SetItem(pyobj,18,PyFloat_FromDouble(obj->get_ramp_30()));
        PyList_SetItem(pyobj,19,PyFloat_FromDouble(obj->get_ramp_q()));
        PyList_SetItem(pyobj,20,PyFloat_FromDouble(obj->get_apf()));
        if ( enable_opf )
        {
            PyList_SetItem(pyobj,21,PyFloat_FromDouble(obj->get_mu_Pmax()));
            PyList_SetItem(pyobj,22,PyFloat_FromDouble(obj->get_mu_Pmin()));
            PyList_SetItem(pyobj,23,PyFloat_FromDouble(obj->get_mu_Qmax()));
            PyList_SetItem(pyobj,24,PyFloat_FromDouble(obj->get_mu_Qmin()));
        }
    }

    // run solver
    PyObject *result = PyObject_CallOneArg(solver,data);
    if ( result && Py_IsTrue(result) )
    {
        // copy values back from solver
        for ( size_t n = 0 ; n < nbus ; n++ )
        {
            bus *obj = buslist[n];
            PyObject *pyobj = PyList_GetItem(busdata,n);
            obj->set_bus_i(PyLong_AsLong(PyList_GET_ITEM(pyobj,0)));
            obj->set_type(PyLong_AsLong(PyList_GET_ITEM(pyobj,1)));
            obj->set_Pd(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,2)));
            obj->set_Qd(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,3)));
            obj->set_Gs(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,4)));
            obj->set_Bs(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,5)));
            obj->set_area(PyLong_AsLong(PyList_GET_ITEM(pyobj,6)));
            obj->set_Vm(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,7)));
            obj->set_Va(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,8)));
            obj->set_baseKV(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,9)));
            obj->set_zone(PyLong_AsLong(PyList_GET_ITEM(pyobj,10)));
            obj->set_Vmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,11)));
            obj->set_Vmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,12)));

            if ( enable_opf )
            {
                obj->set_lam_P(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,13)));
                obj->set_lam_Q(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,14)));
                obj->set_mu_Vmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,15)));
                obj->set_mu_Vmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,16)));
            }
        }
        for ( size_t n = 0 ; n < nbranch ; n++ )
        {
            branch *obj = branchlist[n];
            PyObject *pyobj = PyList_GetItem(branchdata,n);
            obj->set_fbus(PyLong_AsLong(PyList_GET_ITEM(pyobj,0)));
            obj->set_tbus(PyLong_AsLong(PyList_GET_ITEM(pyobj,1)));
            obj->set_r(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,2)));
            obj->set_x(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,3)));
            obj->set_b(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,4)));
            obj->set_rateA(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,5)));
            obj->set_rateB(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,6)));
            obj->set_rateC(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,7)));
            obj->set_ratio(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,8)));
            obj->set_angle(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,9)));
            obj->set_status(PyLong_AsLong(PyList_GET_ITEM(pyobj,10)));
            obj->set_angmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,11)));
            obj->set_angmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,12)));
        }
        for ( size_t n = 0 ; n < ngen ; n++ )
        {
            gen *obj = genlist[n];
            PyObject *pyobj = PyList_GetItem(gendata,n);
            obj->set_bus(PyLong_AsLong(PyList_GET_ITEM(pyobj,0)));
            obj->set_Pg(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,1)));
            obj->set_Qg(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,2)));
            obj->set_Qmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,3)));
            obj->set_Qmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,4)));
            obj->set_Vg(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,5)));
            obj->set_mBase(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,6)));
            obj->set_status(PyLong_AsLong(PyList_GET_ITEM(pyobj,7)));
            obj->set_Pmax(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,8)));
            obj->set_Pmin(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,9)));
            obj->set_Pc1(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,10)));
            obj->set_Pc2(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,11)));
            obj->set_Qc1min(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,12)));
            obj->set_Qc1max(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,13)));
            obj->set_Qc2min(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,14)));
            obj->set_Qc2max(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,15)));
            obj->set_ramp_agc(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,16)));
            obj->set_ramp_10(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,17)));
            obj->set_ramp_30(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,18)));
            obj->set_ramp_q(PyFloat_AsDouble(PyList_GET_ITEM(pyobj,19)));
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
    else
    {
        gl_warning("solver failed");
    }
    if ( result )
    {
        Py_DECREF(result);
    }

    if ( stop_on_failure )
    {
        return TS_INVALID;
    }
    else
    { 
        return maximum_timestep > 0 ? t0+maximum_timestep : TS_NEVER;
    }
}

EXPORT int do_kill(void*)
{
    // if global memory needs to be released, this is a good time to do it
    return 0;
}

EXPORT int check(){
    // if any assert objects have bad filenames, they'll fail on init()
    return 0;
}
