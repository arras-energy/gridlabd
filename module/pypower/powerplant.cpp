// module/pypower/powerplant.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(powerplant);
EXPORT_INIT(powerplant);
EXPORT_SYNC(powerplant);

CLASS *powerplant::oclass = NULL;
powerplant *powerplant::defaults = NULL;

powerplant::powerplant(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"powerplant",sizeof(powerplant),PC_PRETOPDOWN|PC_BOTTOMUP|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class powerplant";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_char32, "city", get_city_offset(),
				PT_DESCRIPTION, "City in which powerplant is located",
			
			PT_char32, "state", get_state_offset(),
				PT_DESCRIPTION, "State in which powerplant is located",
			
			PT_char32, "zipcode", get_zipcode_offset(),
				PT_DESCRIPTION, "Zipcode in which powerplant is located",
			
			PT_char32, "country", get_country_offset(),
				PT_DESCRIPTION, "Country in which powerplant is located",
			
			PT_char32, "naics_code", get_naics_code_offset(),
				PT_DESCRIPTION, "Powerplant NAICS code",
			
			PT_char256, "naics_description", get_naics_description_offset(),
				PT_DESCRIPTION, "Powerplant NAICS description",
			
			PT_char32, "plant_code", get_plant_code_offset(),
				PT_DESCRIPTION, "Generator plant code number",
			
			PT_set, "generator", get_generator_offset(), 
			    PT_KEYWORD, "UNKNOWN", (set)0x00000001, 
			    PT_KEYWORD, "HT", (set)0x00000002, // hydro turbine
			    PT_KEYWORD, "ST", (set)0x00000004, // steam turbine
			    PT_KEYWORD, "AT", (set)0x00000008, // compressed air turbine
			    PT_KEYWORD, "IC", (set)0x00000010, // internal combustion
			    PT_KEYWORD, "FW", (set)0x00000020, // flywheel
			    PT_KEYWORD, "WT", (set)0x00000040, // wind turbine
			    PT_KEYWORD, "ES", (set)0x00000080, // energy storage inverter
			    PT_KEYWORD, "CT", (set)0x00000100, // combustion turbine
			    PT_KEYWORD, "PV", (set)0x00000200, // photovoltaic inverter
			    PT_KEYWORD, "CC", (set)0x00000400, // combined cycle turbine
				PT_DESCRIPTION, "Generator type",

			PT_set, "fuel", get_fuel_offset(), 
			    PT_KEYWORD, "ELEC", (set)0x00000001, 
			    PT_KEYWORD, "WIND", (set)0x00000002,
			    PT_KEYWORD, "SUN", (set)0x00000004, 
			    PT_KEYWORD, "GEO", (set)0x00000008, 
			    PT_KEYWORD, "COKE", (set)0x00000010, 
			    PT_KEYWORD, "WASTE", (set)0x00000020, 
			    PT_KEYWORD, "BIO", (set)0x00000040, 
			    PT_KEYWORD, "OIL", (set)0x00000080, 
			    PT_KEYWORD, "UNKNOWN", (set)0x00000100, 
			    PT_KEYWORD, "WOOD", (set)0x00000200, 
			    PT_KEYWORD, "OTHER", (set)0x00000400, 
			    PT_KEYWORD, "GAS", (set)0x00000800, 
			    PT_KEYWORD, "NUC", (set)0x00001000, 
			    PT_KEYWORD, "WATER", (set)0x00002000, 
			    PT_KEYWORD, "COAL", (set)0x00004000, 
			    PT_KEYWORD, "NG", (set)0x00008000, 
				PT_DESCRIPTION, "Generator fuel type",

			PT_enumeration, "status", get_status_offset(),
				PT_KEYWORD, "OFFLINE", (enumeration)0x00,
				PT_KEYWORD, "ONLINE", (enumeration)0x01,
				PT_DESCRIPTION, "Generator status",

			PT_double, "operating_capacity[MW]", get_operating_capacity_offset(),
				PT_DESCRIPTION, "Generator normal operating capacity (MW)",
			
			PT_double, "summer_capacity[MW]", get_summer_capacity_offset(),
				PT_DESCRIPTION, "Generator summer operating capacity (MW)",
			
			PT_double, "winter_capacity[MW]", get_winter_capacity_offset(),
				PT_DESCRIPTION, "Generator winter operating capacity (MW)",
			
			PT_double, "capacity_factor[pu]", get_capacity_factor_offset(),
				PT_DESCRIPTION, "Generator capacity factor (pu)",
			
			PT_char256, "substation_1", get_substation_1_offset(),
				PT_DESCRIPTION, "Substation 1 id",

			PT_char256, "substation_2", get_substation_2_offset(),
				PT_DESCRIPTION, "Substation 2 id",

			PT_complex, "S[MVA]", get_S_offset(),
				PT_DESCRIPTION, "power generation (MVA)",

			PT_char256, "controller", get_controller_offset(),
				PT_DESCRIPTION,"controller python function name",

			NULL) < 1 )
		{
				throw "unable to publish powerplant properties";
		}
	}
}

int powerplant::create(void) 
{
	py_controller = NULL;
	py_args = PyTuple_New(1);
	py_kwargs = PyDict_New();

	return 1; // return 1 on success, 0 on failure
}

int powerplant::init(OBJECT *parent_hdr)
{
	gen *parent = (gen*)get_parent();
	if ( parent ) 
	{
		if ( parent->isa("gen","pypower") )
		{
			is_dynamic = TRUE;
		}
		else if ( parent->isa("bus","pypower") )
		{
			is_dynamic = FALSE;
		}
		else
		{
			error("parent '%s' is not a pypower bus or gen object",get_parent()->get_name());
			return 0;
		}
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
	PyDict_SetItemString(py_kwargs,"city",PyUnicode_FromString(get_city()));
	PyDict_SetItemString(py_kwargs,"state",PyUnicode_FromString(get_state()));
	PyDict_SetItemString(py_kwargs,"zipcode",PyUnicode_FromString(get_zipcode()));
	PyDict_SetItemString(py_kwargs,"country",PyUnicode_FromString(get_country()));
	PyDict_SetItemString(py_kwargs,"naics_code",PyUnicode_FromString(get_naics_code()));
	PyDict_SetItemString(py_kwargs,"naics_description",PyUnicode_FromString(get_naics_description()));
	PyDict_SetItemString(py_kwargs,"plant_code",PyUnicode_FromString(get_plant_code()));
	PyDict_SetItemString(py_kwargs,"generator",PyLong_FromLong(get_generator()));
	PyDict_SetItemString(py_kwargs,"fuel",PyLong_FromLong(get_fuel()));
	PyDict_SetItemString(py_kwargs,"operating_capacity",PyFloat_FromDouble(get_operating_capacity()));
	PyDict_SetItemString(py_kwargs,"summer_capacity",PyFloat_FromDouble(get_summer_capacity()));
	PyDict_SetItemString(py_kwargs,"winter_capacity",PyFloat_FromDouble(get_winter_capacity()));
	PyDict_SetItemString(py_kwargs,"capacity_factor",PyFloat_FromDouble(get_capacity_factor()));
	PyDict_SetItemString(py_kwargs,"substation_1",PyUnicode_FromString(get_substation_1()));
	PyDict_SetItemString(py_kwargs,"substation_2",PyUnicode_FromString(get_substation_2()));
	Py_complex z = {get_S().Re(), get_S().Im()};
	PyDict_SetItemString(py_kwargs,"S",PyComplex_FromCComplex(z));
	if ( get_parent() && get_parent()->isa("bus","pypower") )
	{
		bus *parent = (bus*)get_parent();
		PyDict_SetItemString(py_kwargs,"Vm",PyFloat_FromDouble(parent->get_Vm()));
		PyDict_SetItemString(py_kwargs,"Va",PyFloat_FromDouble(parent->get_Va()));
	}
	PyDict_SetItemString(py_kwargs,"controller",PyUnicode_FromString(get_controller()));
	PyDict_SetItemString(py_kwargs,"t",PyFloat_FromDouble((double)gl_globalclock));

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP powerplant::presync(TIMESTAMP t0)
{
	// copy data to parent
	if ( is_dynamic ) // gen parent
	{
		if ( S.Re() != 0 || S.Im() != 0 )
		{
			gen *parent = (gen*)get_parent();
			parent->set_Pg(parent->get_Pg()+S.Re());
			parent->set_Qg(parent->get_Qg()+S.Im());
		}
	}
	else // bus parent
	{
		if ( S.Re() != 0 || S.Im() != 0 )
		{
			bus *parent = (bus*)get_parent();
			parent->set_Pd(parent->get_Pd()-S.Re());
			parent->set_Qd(parent->get_Qd()-S.Im());
		}
	}
	return TS_NEVER;
}

TIMESTAMP powerplant::sync(TIMESTAMP t0)
{
	TIMESTAMP t1 = TS_NEVER;

	if ( py_controller )
	{
		Py_complex z = {get_S().Re(), get_S().Im()};
		PyDict_SetItemString(py_kwargs,"S",PyComplex_FromCComplex(z));
		if ( get_parent() && get_parent()->isa("bus","pypower") )
		{
			bus *parent = (bus*)get_parent();
			PyDict_SetItemString(py_kwargs,"Vm",PyFloat_FromDouble(parent->get_Vm()));
			PyDict_SetItemString(py_kwargs,"Va",PyFloat_FromDouble(parent->get_Va()));
		}
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
	return t1;
}

TIMESTAMP powerplant::postsync(TIMESTAMP t0)
{
	// cannot separate contribution of this powerplant to total gen Pg,Qg
	exception("invalid postsync event requrest");
	return TS_NEVER;
}
