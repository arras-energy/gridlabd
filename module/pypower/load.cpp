// module/pypower/load.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(load);
EXPORT_INIT(load);
EXPORT_SYNC(load);

CLASS *load::oclass = NULL;
load *load::defaults = NULL;

load::load(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"load",sizeof(load),PC_PRETOPDOWN|PC_BOTTOMUP|PC_POSTTOPDOWN|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class load";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_complex, "S[MVA]", get_S_offset(),
				PT_DESCRIPTION, "power demand (MVA)",

			PT_complex, "Z[Ohm]", get_Z_offset(),
				PT_DESCRIPTION, "constant impedance load (Ohm)",

			PT_complex, "I[A]", get_I_offset(),
				PT_DESCRIPTION, "constant current load (A)",

			PT_complex, "P[MVA]", get_P_offset(),
				PT_DESCRIPTION, "constant power load (MVA)",

			PT_complex, "V[pu*V]", get_V_offset(),
				PT_DESCRIPTION, "bus voltage (V)",

			PT_double, "Vn[kV]", get_Vn_offset(),
				PT_DESCRIPTION, "nominal voltage (kV)",

			PT_enumeration, "status", get_status_offset(),
				PT_DESCRIPTION, "load status",
				PT_KEYWORD, "OFFLINE", (enumeration)0,
				PT_KEYWORD, "ONLINE", (enumeration)1,
				PT_KEYWORD, "CURTAILED", (enumeration)2,

			PT_double, "response[pu]", get_response_offset(),
				PT_DESCRIPTION, "curtailment response as fractional load reduction",

			PT_char256, "controller", get_controller_offset(),
				PT_DESCRIPTION,"controller python function name",

			NULL) < 1 )
		{
				throw "unable to publish load properties";
		}
	}
}

int load::create(void) 
{
	py_controller = NULL;
	py_args = PyTuple_New(1);
	py_kwargs = PyDict_New();

	return 1; // return 1 on success, 0 on failure
}

int load::init(OBJECT *parent_hdr)
{
	bus *parent = (bus*)get_parent();
	if ( parent && ! parent->isa("bus","pypower") )
	{
		error("parent '%s' is not a pypower bus object",get_parent()->get_name());
		return 0;
	}

	if ( Vn <= 0.0 )
	{
		Vn = parent->get_baseKV();
		if ( Vn == 0.0 )
		{
			error("nominal voltage not specified or inferred from bus");
			return 0;
		}
	}
	else if ( parent->get_baseKV() > 0 && fabs(Vn - parent->get_baseKV()) > Vn*1e-3 )
	{
		warning("nominal voltage Vn differs from bus baseKV by more than 0.1%");
	}

	extern PyObject *py_globals;
	if ( py_globals != NULL && controller[0] != '\0' )
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
	Py_complex z = {get_S().Re(), get_S().Im()};
	PyDict_SetItemString(py_kwargs,"S",PyComplex_FromCComplex(z));
	z.real = get_Z().Re(); z.imag = get_Z().Im(); 
	PyDict_SetItemString(py_kwargs,"Z",PyComplex_FromCComplex(z));
	z.real = get_I().Re(); z.imag = get_I().Im(); 
	PyDict_SetItemString(py_kwargs,"I",PyComplex_FromCComplex(z));
	z.real = get_P().Re(); z.imag = get_P().Im(); 
	PyDict_SetItemString(py_kwargs,"P",PyComplex_FromCComplex(z));
	z.real = get_V().Re(); z.imag = get_V().Im(); 
	PyDict_SetItemString(py_kwargs,"V",PyComplex_FromCComplex(z));
	PyDict_SetItemString(py_kwargs,"status",PyLong_FromLong(get_status()));
	PyDict_SetItemString(py_kwargs,"response",PyFloat_FromDouble(get_response()));
	PyDict_SetItemString(py_kwargs,"t",PyFloat_FromDouble((double)gl_globalclock));

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP load::presync(TIMESTAMP t0)
{
	// calculate load based on voltage and ZIP values
	complex Vpu = V / Vn;
	S = complex(0,0);
	enumeration status = get_status();
	if ( status != LS_OFFLINE )
	{
		S = P + Vpu * ~I;
		if ( Z.Re() != 0 || Z.Im() != 0 )
		{
			S += (~Vpu*Vpu) / ~Z;
		}
		if ( status == LS_CURTAILED)
		{
			S *= 1.0 - get_response();
		}
	}

	// copy load data to parent
	if ( S.Re() != 0.0 || S.Im() != 0.0 )
	{
		bus *parent = (bus*)get_parent();
		if ( parent )
		{
			parent->set_Pd(parent->get_Pd()+S.Re());
			parent->set_Qd(parent->get_Qd()+S.Im());
		}
	}
	return TS_NEVER;
}

TIMESTAMP load::sync(TIMESTAMP t0)
{
	TIMESTAMP t1 = TS_NEVER;
	int nchanges = 0;
	if ( py_controller )
	{
		Py_complex z = {get_S().Re(), get_S().Im()};
		PyDict_SetItemString(py_kwargs,"S",PyComplex_FromCComplex(z));
		z.real = get_Z().Re(); z.imag = get_Z().Im(); 
		PyDict_SetItemString(py_kwargs,"Z",PyComplex_FromCComplex(z));
		z.real = get_I().Re(); z.imag = get_I().Im(); 
		PyDict_SetItemString(py_kwargs,"I",PyComplex_FromCComplex(z));
		z.real = get_P().Re(); z.imag = get_P().Im(); 
		PyDict_SetItemString(py_kwargs,"P",PyComplex_FromCComplex(z));
		z.real = get_V().Re(); z.imag = get_V().Im(); 
		PyDict_SetItemString(py_kwargs,"V",PyComplex_FromCComplex(z));
		PyDict_SetItemString(py_kwargs,"status",PyLong_FromLong(get_status()));
		PyDict_SetItemString(py_kwargs,"response",PyFloat_FromDouble(get_response()));
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
					t1 = (TIMESTAMP)PyFloat_AsDouble(value);
				}
				else
				{
					gld_property prop(my(),name);
					Py_DECREF(repr);

					if ( prop.is_valid() )
					{
						repr = PyObject_Str(value);
						const char *data = PyUnicode_AsUTF8(repr);
						if ( prop.from_string(data) < 0 )
						{
							warning("controller return value %s='%s' is not accepted",name,data);
						}
						nchanges++;
						Py_DECREF(repr);
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
	return nchanges > 0 && t1 == TS_NEVER ? t0 : t1;
}

TIMESTAMP load::postsync(TIMESTAMP t0)
{
	// copy voltage data from parent
	if ( get_status() != LS_OFFLINE )
	{
		bus *parent = (bus*)get_parent();
		if ( parent ) 
		{
			V.SetPolar(parent->get_Vm()*Vn,parent->get_Va());
		}
	}
	else
	{
		V = complex(0,0);
	}
	return TS_NEVER;
}
