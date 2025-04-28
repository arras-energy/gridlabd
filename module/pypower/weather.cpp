// module/pypower/weather.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"
#include <time.h>

EXPORT_CREATE(weather);
EXPORT_INIT(weather);
EXPORT_PRECOMMIT(weather);

CLASS *weather::oclass = NULL;
weather *weather::defaults = NULL;

char256 weather::timestamp_format = ""; // "%Y-%m-%d %H:%M:%S%z"; // RFC-822/ISO8601 standard timestamp

weather::weather(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"weather",sizeof(weather),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class weather";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_char1024, "file", get_file_offset(),
				PT_DESCRIPTION, "Source object for weather data",

			PT_char1024, "variables", get_variables_offset(),
				PT_DESCRIPTION, "Weather variable column names (col1,col2,...)",

			PT_double, "resolution[s]", get_resolution_offset(),
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

			PT_double, "Ws[m/s]", get_Ws_offset(),
				PT_DESCRIPTION, "Wind speed (m/s)",

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

			NULL)<1)
		{
				throw "unable to publish weather properties";
		}

	    gl_global_create("pypower::timestamp_format",
	        PT_char256, &timestamp_format, 
	        PT_DESCRIPTION, "Format for weather file timestamps ('' is RFC822/ISO8601)",
	        NULL);
	}
}

int weather::create(void) 
{
	// initialize weather data
	current = first = last = NULL;

	return 1; // return 1 on success, 0 on failure
}

int weather::init(OBJECT *parent)
{
	// load weather data, if any
	if ( get_file()[0] != '\0' && ! load_weather() )
	{
		error("unable to load weather_file '%s'",(const char*)get_file());
		return 0;
	}

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP weather::precommit(TIMESTAMP t0)
{
	get_weather(t0);

	return current && current->next ? current->next->t : TS_NEVER;	
}

bool weather::load_weather()
{
	// setup weather data
	char *varlist = strdup(get_variables());
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
	FILE *fp = fopen(get_file(),"rt");
	if ( fp == NULL )
	{
		error("file '%s' open for read failed",(const char*)get_file());
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
			error("%s@%d: timestamp '%s' is not valid",(const char*)get_file(),lineno,buffer);
			result = false;
			break;
		}
		time_t tu = (TIMESTAMP)t;
		if ( get_resolution() > 0 && tu % (long long)get_resolution() == 0 )
		{
			if ( ! add_weather(tu,data) )
			{
				error("%s@%d: weather data read failed",(const char*)get_file(),lineno);
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

bool weather::add_weather(TIMESTAMP t, char *buffer)
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

bool weather::get_weather(TIMESTAMP t)
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
