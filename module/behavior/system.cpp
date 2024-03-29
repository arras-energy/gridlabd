// module/behavior/system.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "behavior.h"

EXPORT_CREATE(system);
EXPORT_INIT(system);
EXPORT_PRECOMMIT(system);
EXPORT_METHOD(system,u);
EXPORT_METHOD(system,p);
EXPORT_METHOD(system,Z);

CLASS *system::oclass = NULL;
class system *system::defaults = NULL;

int32 system::limit_retries = 1000;

system::system(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"system",sizeof(system),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class system";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_double, "tau", get_tau_offset(),
				PT_DESCRIPTION, "System activity",

			PT_double, "mu", get_mu_offset(),
				PT_DESCRIPTION, "Asset potential",

			PT_int64, "N", get_N_offset(),
				PT_DESCRIPTION, "Number of devices",

			PT_method, "u", get_u_offset(),
				PT_DESCRIPTION, "State value",

			PT_method, "p", get_p_offset(),
				PT_DESCRIPTION, "State probability",

			PT_method, "Z", get_Z_offset(),
				PT_DESCRIPTION, "State partition function",

			NULL)<1)
		{
				throw "unable to publish system properties";
		}
	}
}

int system::create(void) 
{
	n_points = 0;
	max_points = 1024;
	point_list = (gld_property**)malloc(sizeof(gld_property*)*max_points);
	name_list = (char **)malloc(sizeof(char*)*max_points);
	point_names = (char*)malloc(1);
	point_names[0] = '\0';
	return 1; // return 1 on success, 0 on failure
}

int system::init(OBJECT *parent)
{
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP system::precommit(TIMESTAMP t0)
{
	return TS_NEVER;
}

int system::u(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// get size of output buffer needed
		return strlen(point_names);
	}
	else if ( len == 0 )
	{
		// read data from buffer
		int len = 0;
		return len;
	}
	else
	{
		// write to buffer
		return 0;
	}
}

int system::p(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// get size of output buffer needed
		return strlen(point_names);
	}
	else if ( len == 0 )
	{
		// read data from buffer
		int len = 0;
		return len;
	}
	else
	{
		// write to buffer
		return 0;
	}
}

int system::Z(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// get size of output buffer needed
		return strlen(point_names);
	}
	else if ( len == 0 )
	{
		// read data from buffer
		int len = 0;
		return len;
	}
	else
	{
		// write to buffer
		return 0;
	}
}
