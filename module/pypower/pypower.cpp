// module/pypower/main.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#define DLMAIN

#include "pypower.h"

#include "Python.h"

bool enable_opf = false;
double base_MVA = 100.0;
int32 pypower_version = 2;

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

    gl_global_create("pypower::version",
        PT_int32, &pypower_version, 
        PT_DESCRIPTION, "Version of pypower used",
        NULL);

    gl_global_create("pypower::enable_opf",
        PT_bool, &enable_opf, 
        PT_DESCRIPTION, "Flag to enable optimal powerflow (OPF) solver",
        NULL);

    gl_global_create("pypower::baseMVA",
        PT_double, &base_MVA, 
        PT_UNITS, "MVA", 
        PT_DESCRIPTION, "Base MVA value",
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
        PyList_SET_ITEM(busdata,n,PyList_New(17));
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
        PyList_SET_ITEM(gendata,n,PyList_New(21));
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
        PyList_SET_ITEM(pyobj,0,PyLong_FromLong(obj->get_bus_i()));
        PyList_SET_ITEM(pyobj,1,PyLong_FromLong(obj->get_type()));
        PyList_SET_ITEM(pyobj,2,PyFloat_FromDouble(obj->get_Pd()));
        PyList_SET_ITEM(pyobj,3,PyFloat_FromDouble(obj->get_Qd()));
        PyList_SET_ITEM(pyobj,4,PyFloat_FromDouble(obj->get_Gs()));
        PyList_SET_ITEM(pyobj,5,PyFloat_FromDouble(obj->get_Bs()));
        PyList_SET_ITEM(pyobj,6,PyLong_FromLong(obj->get_area()));
        PyList_SET_ITEM(pyobj,7,PyFloat_FromDouble(obj->get_Vm()));
        PyList_SET_ITEM(pyobj,8,PyFloat_FromDouble(obj->get_Va()));
        PyList_SET_ITEM(pyobj,9,PyFloat_FromDouble(obj->get_baseKV()));
        PyList_SET_ITEM(pyobj,10,PyLong_FromLong(obj->get_zone()));
        PyList_SET_ITEM(pyobj,11,PyFloat_FromDouble(obj->get_Vmax()));
        PyList_SET_ITEM(pyobj,12,PyFloat_FromDouble(obj->get_Vmin()));
    }

    // run solver
    PyObject *result = PyObject_CallOneArg(solver,data);
    if ( Py_IsTrue(result) )
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
    }
    else
    {
        gl_warning("solver failed");
    }
    Py_DECREF(result);


    return TS_NEVER;
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
