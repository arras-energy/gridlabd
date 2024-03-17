// module/pypower/relay.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(relay);
EXPORT_INIT(relay);
EXPORT_SYNC(relay);

CLASS *relay::oclass = NULL;
relay *relay::defaults = NULL;

relay::relay(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"relay",sizeof(relay),PC_BOTTOMUP|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class relay";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_enumeration, "status", get_status_offset(),
				PT_DEFAULT, "CLOSED",
				PT_KEYWORD, "CLOSED", (enumeration)RS_CLOSED,
				PT_KEYWORD, "OPEN", (enumeration)RS_OPEN,
				PT_DESCRIPTION, "relay status (OPEN or CLOSED)",

			PT_char256, "controller", get_controller_offset(),
				PT_DESCRIPTION,"controller python function name",

			NULL) < 1 )
		{
				throw "unable to publish relay properties";
		}
	}
}

int relay::create(void) 
{
	py_controller = NULL;
	py_args = PyTuple_New(1);
	py_kwargs = PyDict_New();

	return 1; // return 1 on success, 0 on failure
}

int relay::init(OBJECT *parent_hdr)
{
	branch *parent = (branch*)get_parent();
	if ( parent ) 
	{
		if ( ! parent->isa("branch","pypower") )
		{
			error("relay parent must by a pypower branch");
			return 0;
		}
	}
	else
	{
		warning("relay without parent does nothing");
		return 1;
	}

	// setup controller
	extern PyObject *py_globals;
	if ( controller[0] == '\0' )
	{
		warning("relay has no controller");
	}
	else if ( py_globals != NULL )
	{
		py_controller = PyDict_GetItemString(py_globals,controller);
		if ( py_controller == NULL )
		{
			error("pypower controller '%s' is not found",(const char *)controller);
			return 0;			
		}
		if ( ! PyCallable_Check(py_controller) )
		{
			Py_DECREF(py_controller);
			error("pypower controller '%s' is not callable",(const char *)controller);
			return 0;
		}

		if ( get_name() )
		{
			PyTuple_SET_ITEM(py_args,0,PyUnicode_FromString(get_name()));
		}
		else
		{
			char buffer[80];
			snprintf(buffer,sizeof(buffer)-1,"%64s:%ld",get_oclass()->get_name(),(long)get_id());
			PyTuple_SET_ITEM(py_args,0,PyUnicode_FromString(buffer));
		}

		PyDict_SetItemString(py_kwargs,"tbus",PyLong_FromLong(parent->get_tbus()));
		PyDict_SetItemString(py_kwargs,"r",PyFloat_FromDouble(parent->get_r()));
		PyDict_SetItemString(py_kwargs,"x",PyFloat_FromDouble(parent->get_x()));
		PyDict_SetItemString(py_kwargs,"b",PyFloat_FromDouble(parent->get_b()));
		PyDict_SetItemString(py_kwargs,"rateA",PyFloat_FromDouble(parent->get_rateA()));
		PyDict_SetItemString(py_kwargs,"rateB",PyFloat_FromDouble(parent->get_rateB()));
		PyDict_SetItemString(py_kwargs,"rateC",PyFloat_FromDouble(parent->get_rateC()));
		PyDict_SetItemString(py_kwargs,"ratio",PyFloat_FromDouble(parent->get_ratio()));
		PyDict_SetItemString(py_kwargs,"angle",PyFloat_FromDouble(parent->get_angle()));
		PyDict_SetItemString(py_kwargs,"status",PyLong_FromLong(parent->get_status()));
		PyDict_SetItemString(py_kwargs,"angmin",PyFloat_FromDouble(parent->get_angmin()));
		PyDict_SetItemString(py_kwargs,"angmax",PyFloat_FromDouble(parent->get_angmax()));
		PyDict_SetItemString(py_kwargs,"controller",PyUnicode_FromString(get_controller()));
		PyDict_SetItemString(py_kwargs,"t",PyFloat_FromDouble((double)gl_globalclock));
	}
	else
	{
		error("unable to find global controllers file");
		return 0;
	}


	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP relay::sync(TIMESTAMP t0)
{
	TIMESTAMP t1 = TS_NEVER;
	branch *parent = (branch*)get_parent();
	if ( parent == NULL )
	{
		return TS_NEVER;
	}

	if ( py_controller )
	{
		PyDict_SetItemString(py_kwargs,"status",PyLong_FromLong(parent->get_status()==branch::BS_IN?RS_CLOSED:RS_OPEN));
		PyDict_SetItemString(py_kwargs,"controller",PyUnicode_FromString(get_controller()));
		PyDict_SetItemString(py_kwargs,"t",PyFloat_FromDouble((double)gl_globalclock));
		PyObject *result = PyObject_Call(py_controller,py_args,py_kwargs);
		if ( result == NULL )
		{
	        if ( PyErr_Occurred() )
            {
                PyErr_Print();
            }
            else
            {
            	error("controller call failed (no info)");
            }

            extern bool stop_on_failure;
            if ( stop_on_failure )
            {
	            return TS_INVALID;
	        }
		}
		else if ( PyDict_Check(result) )
		{
			PyObject *key, *value;
			Py_ssize_t pos = 0;
			while ( PyDict_Next(result,&pos,&key,&value) )
			{
				PyObject *repr = PyObject_Str(key);
				const char *name = PyUnicode_AsUTF8(repr);
				if ( strcmp(name,"t") == 0 )
				{
					t1 = (TIMESTAMP)PyFloat_AsDouble(value); // specifies next update time
				}
				else
				{
					gld_property prop(my(),name);
					Py_DECREF(repr);

					if ( prop.is_valid() )
					{
						repr = PyObject_Str(value);
						const char *data = PyUnicode_AsUTF8(repr);
						prop.from_string(data);
						Py_DECREF(repr);
						t1 = t0; // force iteration
					}
					else
					{
						error("controller return property '%s' is not valid",name);
					}
				}
			}
			Py_DECREF(result);
		}
		else 
		{
			error("controller return value not a property update dictionary");
			Py_DECREF(result);
		}		
	}

	parent->set_status(get_status()==RS_CLOSED ? branch::BS_IN : branch::BS_OUT);

	return t1;
}

