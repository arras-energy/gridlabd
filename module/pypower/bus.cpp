// module/pypower/bus.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"
#include <time.h>

EXPORT_CREATE(bus);
EXPORT_INIT(bus);
EXPORT_SYNC(bus);
EXPORT_PRECOMMIT(bus);

CLASS *bus::oclass = NULL;
bus *bus::defaults = NULL;

static int last_i = 0;
char256 bus::timestamp_format = ""; // "%Y-%m-%d %H:%M:%S%z"; // RFC-822/ISO8601 standard timestamp

bus::bus(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"bus",sizeof(bus),PC_PRETOPDOWN|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class bus";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,
			PT_int32, "bus_i", get_bus_i_offset(),
				PT_DESCRIPTION, "bus number (1 to 29997)",

			PT_complex, "S[MVA]", get_Pd_offset(),
				PT_DESCRIPTION, "base load demand not counting child objects, including weather sensitivities, copied to Pd,Qd by default (MVA)",

			PT_enumeration, "type", get_type_offset(),
				PT_DESCRIPTION, "bus type (1 = PQ, 2 = PV, 3 = ref, 4 = isolated)",
				PT_KEYWORD, "UNKNOWN", (enumeration)0,
				PT_KEYWORD, "PQ", (enumeration)1,
				PT_KEYWORD, "PV", (enumeration)2,
				PT_KEYWORD, "REF", (enumeration)3,
				PT_KEYWORD, "NONE", (enumeration)4,
				PT_KEYWORD, "PQREF", (enumeration)1,

			PT_double, "Pd[MW]", get_Pd_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "real power demand (MW)",

			PT_double, "Qd[MVAr]", get_Qd_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "reactive power demand (MVAr)",

			PT_double, "Gs[MW]", get_Gs_offset(),
				PT_DESCRIPTION, "shunt conductance (MW at V = 1.0 p.u.)",

			PT_double, "Bs[MVAr]", get_Bs_offset(),
				PT_DESCRIPTION, "shunt susceptance (MVAr at V = 1.0 p.u.)",

			PT_int32, "area", get_area_offset(),
				PT_DESCRIPTION, "area number, 1-100",

			PT_double, "baseKV[kV]", get_baseKV_offset(),
				PT_DESCRIPTION, "voltage magnitude (p.u.)",

			PT_double, "Vm[pu*V]", get_Vm_offset(),
				PT_DESCRIPTION, "voltage angle (degrees)",

			PT_double, "Va[deg]", get_Va_offset(),
				PT_DESCRIPTION, "base voltage (kV)",

			PT_int32, "zone", get_zone_offset(),
				PT_DESCRIPTION, "loss zone (1-999)",

			PT_double, "Vmax[pu*V]", get_Vmax_offset(),
				PT_DEFAULT,"1.2 pu*V",
				PT_DESCRIPTION, "maximum voltage magnitude (p.u.)",

			PT_double, "Vmin[pu*V]", get_Vmin_offset(),
				PT_DEFAULT,"0.8 pu*V",
				PT_DESCRIPTION, "minimum voltage magnitude (p.u.)",

			PT_double, "lam_P", get_lam_P_offset(),
				PT_DESCRIPTION, "Lagrange multiplier on real power mismatch (u/MW)",
				PT_ACCESS, PA_REFERENCE,

			PT_double, "lam_Q", get_lam_Q_offset(),
				PT_DESCRIPTION, "Lagrange multiplier on reactive power mismatch (u/MVAr)",
				PT_ACCESS, PA_REFERENCE,

			PT_double, "mu_Vmax", get_mu_Vmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper voltage limit (u/p.u.)",
				PT_ACCESS, PA_REFERENCE,

			PT_double, "mu_Vmin", get_mu_Vmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower voltage limit (u/p.u.)",
				PT_ACCESS, PA_REFERENCE,

			PT_char1024, "weather_file", get_weather_file_offset(),
				PT_DESCRIPTION, "Source object for weather data",

			PT_char1024, "weather_variables", get_weather_variables_offset(),
				PT_DESCRIPTION, "Weather variable column names (col1,col2,...)",

			PT_double, "weather_resolution[s]", get_weather_resolution_offset(),
				PT_DEFAULT, "3600 s",
				PT_DESCRIPTION, "Weather time downsampling resolution (s)",

			PT_double, "Sn[W/m^2]", get_Sn_offset(),
				PT_DESCRIPTION, "Solar direct normal irradiance (W/m^2)",

			PT_double, "Sh[W/m^2]", get_Sh_offset(),
				PT_DESCRIPTION, "Solar horizontal irradiance (W/m^2)",

			PT_double, "Sg[W/m^2]", get_Sg_offset(),
				PT_DESCRIPTION, "Solar global irradiance (W/m^2)",

			PT_double, "Wd[deg]", get_Wd_offset(),
				PT_DESCRIPTION, "Wind direction (deg)",

			PT_double, "Ws[m/2]", get_Ws_offset(),
				PT_DESCRIPTION, "Wind speed (m/2)",

			PT_double, "Td[degC]", get_Td_offset(),
				PT_DESCRIPTION, "Dry-bulb air temperature (degC)",

			PT_double, "Tw[degC]", get_Tw_offset(),
				PT_DESCRIPTION, "Wet-bulb air temperature (degC)",

			PT_double, "RH[%]", get_RH_offset(),
				PT_DESCRIPTION, "Relative humidity (%)",

			PT_double, "PW[in]", get_PW_offset(),
				PT_DESCRIPTION, "Precipitable_water (in)",

			PT_double, "HI[degF]", get_HI_offset(),
				PT_DESCRIPTION, "Heat index (degF)",

			PT_char1024, "weather_sensitivity", get_weather_sensitivity_offset(),
				PT_DESCRIPTION, "Weather sensitivities {PROP: VAR[ REL VAL],SLOPE[; ...]}",

			NULL)<1)
		{
				throw "unable to publish bus properties";
		}
	}
}

int bus::create(void) 
{
	extern bus *buslist[MAXENT];
	extern size_t nbus;
	if ( nbus < MAXENT )
	{
		buslist[nbus++] = this;
	}
	else
	{
		throw "maximum bus entities exceeded";
	}

	// initialize weather data
	current = first = last = NULL;
	sensitivity_list = NULL;

	return 1; // return 1 on success, 0 on failure
}

int bus::init(OBJECT *parent)
{
	// automatic id number generation
	if ( get_bus_i() == 0 )
	{
		set_bus_i(++last_i);
	}

	// copy demand to base load if baseload not set
	if ( S.Re() == 0.0 && S.Im() == 0.0 )
	{
		S.Re() = Pd;
		S.Im() = Qd;
	}

	// load weather data, if any
	if ( get_weather_file()[0] != '\0' && ! load_weather() )
	{
		error("unable to load weather_file '%s'",(const char*)get_weather_file());
		return 0;
	}

	char buffer[strlen(weather_sensitivity)+1];
	strcpy(buffer,weather_sensitivity);
	char *next=NULL, *last=NULL;
	// fprintf(stderr,"weather_sensitivity = '%s'\n",(const char*)get_weather_sensitivity());
	while ( (next=strtok_r(next?NULL:buffer,";",&last)) != NULL )
	{
		char propname[65], varname[65], cutoff_test='@';
		double cutoff_value=0, slope_value;
		// PROP: VAR[ REL VAL],SLOPE
		// fprintf(stderr,"next = '%s'\n",next);
		if ( sscanf(next,"%64[^:]:%64[^<>]%c%lf,%lf",propname,varname,&cutoff_test,&cutoff_value,&slope_value) == 5 
			|| sscanf(next,"%64[^:]:%64[^,],%lf",propname,varname,&slope_value) == 3 )
		{
			// fprintf(stderr,"sensitivity: %s += %s * %lf if %s %c %lf else 0\n",propname,varname,slope_value,varname,cutoff_test,cutoff_value);
			gld_property source(my(),varname);
			if ( ! source.is_valid() )
			{
				error("weather_sensitivity source '%s' is not valid",varname);
				return 0;
			}
			else if ( source.get_type() != PT_double )
			{
				error("weather_sensitivity source '%s' is not a double",varname);
				return 0;
			}
			SENSITIVITY *sensitivity = new SENSITIVITY;
			if ( strcmp(propname,"P") == 0 || strcmp(propname,"S.real") == 0 )
			{
				sensitivity->value = &S.Re();
			}
			else if ( strcmp(propname,"Q") == 0 || strcmp(propname,"S.imag") == 0 )
			{
				sensitivity->value = &S.Im();
			}
			else
			{
				error("property '%s' is not valid",propname);
			}
			sensitivity->def = strdup(next);
			sensitivity->source = (double*)source.get_addr();
			sensitivity->slope = slope_value;
			sensitivity->cutoff_test = cutoff_test;
			sensitivity->cutoff_value = cutoff_value;
			sensitivity->last_adjustment = 0.0;
			sensitivity->next = sensitivity_list;
			sensitivity_list = sensitivity;
		}
		else
		{
			error("weather_sensitivity '%s' in not valid",next);
			return 0;
		}
	}

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP bus::precommit(TIMESTAMP t0)
{
	get_weather(t0);

	// adjust values with sensitivities
	for ( SENSITIVITY *sensitivity = sensitivity_list ; sensitivity != NULL ; sensitivity = sensitivity->next )
	{
		*(sensitivity->value) -= sensitivity->last_adjustment;
		if ( ( sensitivity->cutoff_test == '<' && *sensitivity->source < sensitivity->cutoff_value )
			|| (sensitivity->cutoff_test == '>' && *sensitivity->source > sensitivity->cutoff_value )
			|| sensitivity->cutoff_test == '@'
			)
		{
			sensitivity->last_adjustment = (*sensitivity->source - sensitivity->cutoff_value) * sensitivity->slope;
			*(sensitivity->value) += sensitivity->last_adjustment;
		}
		else
		{
			sensitivity->last_adjustment = 0.0;
		}
	}

	return current && current->next ? current->next->t : TS_NEVER;	
}

TIMESTAMP bus::presync(TIMESTAMP t0)
{
	// reset to base load
	Pd = S.Re();
	Qd = S.Im();

	return TS_NEVER;
}

TIMESTAMP bus::sync(TIMESTAMP t0)
{
	exception("invalid sync call");
	return TS_NEVER;
}

TIMESTAMP bus::postsync(TIMESTAMP t0)
{
	exception("invalid postsync call");
	return TS_NEVER;
}

bool bus::load_weather()
{
	// setup weather data
	char *varlist = strdup(get_weather_variables());
	char *next=NULL, *last=NULL;
	int n_var = 0;
	while ( (next=strtok_r(next?NULL:varlist,",",&last)) != NULL )
	{
		gld_property *prop = new gld_property(my(),next);
		if ( prop == NULL || ! prop->is_valid() )
		{
			error("weather variable '%s' is not valid",next);
			return 0;
		}
		weather_mapper[n_var++] = prop;
	}
	weather_mapper[n_var] = NULL; // mark end of weather variables with a NULL pointer
	free(varlist);

	// process weather file
	bool result = false;
	FILE *fp = fopen(get_weather_file(),"rt");
	if ( fp == NULL )
	{
		error("file '%s' open for read failed",(const char*)get_weather_file());
		return false;
	}
	char buffer[1024];
	
	for ( int lineno = 0 ; !feof(fp) && fgets(buffer,sizeof(buffer)-1,fp) != NULL ; lineno++ )
	{
		char *data = strchr(buffer,',');
		if ( data == NULL || ! isdigit(buffer[0]) )
		{
			// no/bad data -- ignore line
			continue;
		}
		*data++ = '\0';
		gld_clock t(buffer);
		if ( ! t.is_valid() )
		{
			error("%s@%d: timestamp '%s' is not valid",(const char*)get_weather_file(),lineno,buffer);
			result = false;
			break;
		}
		time_t tu = (TIMESTAMP)t;
		if ( get_weather_resolution() > 0 && tu % (long long)get_weather_resolution() == 0 )
		{
			if ( ! add_weather(tu,data) )
			{
				error("%s@%d: weather data read failed",(const char*)get_weather_file(),lineno);
				result = false;
				break;
			}
		}
		result = true;
	}
	fclose(fp);

	// start with first record
	current = first;

	return result;
}

bool bus::add_weather(TIMESTAMP t, char *buffer)
{
	gld_clock ts(t);

	// check time
	if ( last && t <= last->t )
	{
		error("duplicate or out-of-sequence timestamp (t='%s' <= last->t='%s')",
			gld_clock(t).get_string().get_buffer(),gld_clock(last->t).get_string().get_buffer());
		return false;
	}

	// add new weather record
	WEATHERDATA *data = new WEATHERDATA;
	data->t = t;
	data->next = NULL;
	if ( last != NULL )
	{
		last->next = data;
	}
	last = data;
	if ( first == NULL )
	{
		first = data;
	}

	// parse buffer
	char *next=NULL, *last=NULL;
	int n_var = 0;
	while ( (next=strtok_r(next?NULL:buffer,",",&last)) != NULL )
	{
		data->value[n_var++] = atof(next);
	}
	while ( n_var < N_WEATHERDATA )
	{
		data->value[n_var++] = 0.0;
	}
	return true;
}

bool bus::get_weather(TIMESTAMP t)
{
	if ( last == NULL )
	{
		return true; // no weather
	}
	while ( current && current->t < t )
	{
		current = current->next;
	}
	if ( current == NULL )
	{
		warning("weather data ended unexpectedly");
		return true;
	}
	for ( int n_var = 0 ; n_var < N_WEATHERDATA && weather_mapper[n_var] != NULL ; n_var++ )
	{
		weather_mapper[n_var]->setp(current->value[n_var]);
	}
	return true;
}
