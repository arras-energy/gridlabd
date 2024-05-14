// module/pypower/powerplant.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(powerplant);
EXPORT_INIT(powerplant);
EXPORT_PRECOMMIT(powerplant);
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
			    PT_KEYWORD, "UNKNOWN", (set)GT_UNKNOWN, 
			    PT_KEYWORD, "HT", (set)GT_HYDROTURBINE,
			    PT_KEYWORD, "ST", (set)GT_STEAMTURBINE,
			    PT_KEYWORD, "AT", (set)GT_COMPRESSEDAIR,
			    PT_KEYWORD, "IC", (set)GT_INTERNALCOMBUSTION,
			    PT_KEYWORD, "FW", (set)GT_FLYWHEEL,
			    PT_KEYWORD, "WT", (set)GT_WINDTURBINE,
			    PT_KEYWORD, "ES", (set)GT_ENERGYSTORAGE,
			    PT_KEYWORD, "CT", (set)GT_COMBUSTIONTURBINE,
			    PT_KEYWORD, "PV", (set)GT_PHOTOVOLTAIC,
			    PT_KEYWORD, "CC", (set)GT_COMBINEDCYCLE,
				PT_DESCRIPTION, "Generator type",

			PT_set, "fuel", get_fuel_offset(), 
			    PT_KEYWORD, "ELEC", (set)FT_ELECTRICITY, 
			    PT_KEYWORD, "WIND", (set)FT_WIND,
			    PT_KEYWORD, "SUN", (set)FT_SOLAR, 
			    PT_KEYWORD, "GEO", (set)FT_GEOTHERMAL, 
			    PT_KEYWORD, "COKE", (set)FT_COKE, 
			    PT_KEYWORD, "WASTE", (set)FT_WASTE, 
			    PT_KEYWORD, "BIO", (set)FT_BIOMASS, 
			    PT_KEYWORD, "OIL", (set)FT_OIL, 
			    PT_KEYWORD, "UNKNOWN", (set)FT_UNKNOWN, 
			    PT_KEYWORD, "WOOD", (set)FT_WOOD, 
			    PT_KEYWORD, "OTHER", (set)FT_OTHER, 
			    PT_KEYWORD, "GAS", (set)FT_GAS, 
			    PT_KEYWORD, "NUC", (set)FT_NUCLEAR, 
			    PT_KEYWORD, "WATER", (set)FT_WATER, 
			    PT_KEYWORD, "COAL", (set)FT_COAL, 
			    PT_KEYWORD, "NG", (set)FT_NATURALGAS, 
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

			PT_double, "storage_capacity[MWh]", get_storage_capacity_offset(),
				PT_DESCRIPTION, "Energy storage capacity (MWh)",

			PT_double, "charging_capacity[MW]", get_charging_capacity_offset(),
				PT_DESCRIPTION, "Energy storage charging capacity (MW)",

			PT_double, "storage_efficiency[pu]", get_storage_efficiency_offset(),
				PT_DEFAULT, "1 pu",
				PT_DESCRIPTION, "Energy storage round-trip efficiency (pu)",

			PT_double, "state_of_charge[pu]", get_state_of_charge_offset(),
				PT_DESCRIPTION, "Energy storage state of charge (pu)",

			PT_complex, "S[MVA]", get_S_offset(),
				PT_DESCRIPTION, "power generation (MVA)",

			PT_char256, "controller", get_controller_offset(),
				PT_DESCRIPTION,"controller python function name",

			PT_double, "startup_cost[$/MW]", get_startup_cost_offset(),
				PT_DESCRIPTION,"generator startup cost ($/MW)",

			PT_double, "shutdown_cost[$/MW]", get_shutdown_cost_offset(),
				PT_DESCRIPTION,"generator shutdown cost ($/MW)",

			PT_double, "fixed_cost[$/h]", get_fixed_cost_offset(),
				PT_DESCRIPTION,"generator fixed cost ($/h)",

			PT_double, "variable_cost[$/MWh]", get_variable_cost_offset(),
				PT_DESCRIPTION,"generator variable cost ($/MWh)",

			PT_double, "scarcity_cost[$/MW^2/h]", get_scarcity_cost_offset(),
				PT_DESCRIPTION,"generator scarcity cost ($/MW^2h)",

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
	last_t = 0;

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
			if ( get_storage_capacity() > 0 )
			{
				warning("energy storage devices cannot be dynamically dispatchable (parent is a generator)");
			}
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

		// look for gencost object that corresponds to this generator (if any)
		for ( OBJECT *obj = gl_object_get_first() ; obj != NULL ; obj = obj->next)
		{
			if ( gl_object_isa(obj,"gencost","pypower") )
			{
				costobj = OBJECTDATA(obj,gencost);
				if ( costobj->get_parent() == parent )
				{
					break; // got it
				}
				else
				{
					costobj = NULL; // forget about it!
				}
			}
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

TIMESTAMP powerplant::precommit(TIMESTAMP t0)
{
	if ( last_t > 0 && get_storage_capacity() > 0 )
	{
		double Dt = double(t0-last_t)/3600.0;
		
		double DE = S.Re();
		if ( DE > get_charging_capacity() )
		{
			DE = get_charging_capacity();
		}
		else if ( DE < -get_charging_capacity() )
		{
			DE = -get_charging_capacity();
		}

		double Et = get_storage_capacity()*get_state_of_charge() + DE*Dt*get_storage_efficiency();
		if ( Et > get_storage_capacity() )
		{
			set_state_of_charge(1.0);
		}
		else if ( Et < 0 )
		{
			set_state_of_charge(0.0);
		}
		else
		{
			set_state_of_charge(Et/get_storage_capacity());
		}
	}
	last_t = t0;

	// post costs
	if ( costobj != NULL )
	{
		costobj->set_startup(get_startup_cost());
		costobj->set_shutdown(get_shutdown_cost());
		char buffer[1025];
		snprintf(buffer,sizeof(buffer)-1,"%lf,%lf,%lf",get_scarcity_cost(),get_variable_cost(),get_fixed_cost());
		costobj->set_costs(buffer);
	}

	return TS_NEVER;
}
TIMESTAMP powerplant::presync(TIMESTAMP t0)
{
	if ( get_status() == 0 )
	{
		return TS_NEVER;
	}

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
