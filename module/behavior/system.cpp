// module/behavior/system.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "behavior.h"

EXPORT_CREATE(system);
EXPORT_INIT(system);
EXPORT_PRECOMMIT(system);
EXPORT_METHOD(system,u);
EXPORT_METHOD(system,p);
EXPORT_METHOD(system,device);

CLASS *system::oclass = NULL;
class system *system::defaults = NULL;

double system::resolution = 1e-9;

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

			PT_double, "sigma", get_sigma_offset(),
				PT_DESCRIPTION, "System entropy",

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

			PT_double, "Z", get_Z_offset(),
				PT_DESCRIPTION, "State partition function",

			PT_double, "Navg", get_Navg_offset(),
				PT_DESCRIPTION, "Average number of devices in system",

			PT_double, "Uavg", get_Uavg_offset(),
				PT_DESCRIPTION, "Average device value in system",

			PT_method, "device", get_device_offset(),
				PT_DESCRIPTION, "Property of device connected to this system",

			NULL)<1)
		{
				throw "unable to publish system properties";
		}

	    gl_global_create("behavior::system_resolution",
	        PT_double, &resolution, 
	        PT_DESCRIPTION, "Resolution of system properties",
	        NULL);
	}
}

int system::create(void) 
{
	n_values = 0;
	values = NULL;
	probs = NULL;

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
	if ( n_values < 2 )
	{
		error("there must be at least 2 state values u specified");
		return 0;
	}
	update();
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

void system::update(void)
{
	Z = 0.0;
	Navg = 0.0;
	Uavg = 0.0;
	sigma = 0.0;
	double u_min = 0;
	bool zero_tau = ( fabs(tau) <= resolution );
	if ( ! zero_tau )
	{
		for ( int n = 0 ; n < n_values ; n++ )
		{
			double x = round(exp((N*mu-values[n])/tau)/resolution)*resolution;
			if ( isfinite(x) && ! isnan(x) && x >= resolution && x < 1/resolution )
			{
				probs[n] = x;
				Z += x;
			}
			else
			{
				probs[n] = 0.0;
			}
		}
		if ( fabs(Z) < resolution )
		{
			zero_tau = true;
			Z = 0;
		}
	}
	for ( int n = 0 ; n < n_values ; n++ )
	{
		if ( zero_tau && tau >= 0 )
		{
			u_min = ( n == 0 || values[n] < u_min ? values[n] : u_min );
			probs[n] = 0;
		}
		else if ( zero_tau && tau < 0 )
		{
			u_min = ( n == 0 || values[n] > u_min ? values[n] : u_min );
			probs[n] = 0;
		}
		else
		{
			double x = probs[n];
			Navg += N*x;
			Uavg += values[n]*x;
			if ( probs[n] > 0 )
			{
				sigma += -probs[n]*log(probs[n]);
			}
		}
	}
	if ( zero_tau )
	{
		for ( int n = 0 ; n < n_values ; n++ )
		{
			if ( values[n] == u_min )
			{
				probs[n] = 1;
				Navg += N;
				Uavg += values[n];
				if ( probs[n] > 0 )
				{
					sigma += -probs[n]*log(probs[n]);
				}
				Z++;
			}
		}
	}
	for ( int n = 0 ; n < n_values ; n++ )
	{
		probs[n] = round(probs[n]/Z/resolution)*resolution;
	}
	Navg = round(Navg/Z/resolution)*resolution;
	Uavg = round(Uavg/Z/resolution)*resolution;
	sigma = round(sigma/resolution)*resolution;
	if ( zero_tau )
	{
		Z = 0;
	}

	for ( size_t n = 0 ; n < n_points ; n++ )
	{
		gld_property *prop = point_list[n];
		double r = gl_random_uniform(&(prop->get_object()->rng_state),0,1);
		double rs = 0.0;
		int s;
		for ( s = 0 ; s < n_values ; s++ )
		{
			rs += probs[s];
			if ( r <= rs )
			{
				break;
			}
		}
		if ( s == n_values )
		{
			s = n_values - 1;
		}
		switch ( prop->get_type() )
		{
		case PT_enumeration:
			prop->setp(s);
			break;
		case PT_double:
			prop->setp(values[s]);
			break;
		default:
			break;
		}
	}
}

TIMESTAMP system::precommit(TIMESTAMP t0)
{
	update();
	return TS_NEVER;
}

int system::u(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// get size of output buffer needed
		len = 0;
		for ( int n = 0 ; n < n_values ; n++ )
		{
			int sz = snprintf(NULL,0,"%g",values[n]);
			if ( sz < 0 )
			{
				return -1;
			}
			len += sz + 1;
		}
		return len;
	}
	else if ( len == 0 )
	{
		// read data from buffer
		char *next=NULL, *last=NULL;
		while ( (next=strtok_r(next?NULL:buffer,",",&last)) != NULL )
		{
			values = (double*)realloc(values,(n_values+1)*(sizeof(*values)));
			probs = (double*)realloc(probs,(n_values+1)*(sizeof(*values)));
			if ( values == NULL || probs == NULL )
			{
				exception("memory allocation error reallocating values buffer");
			}
			values[n_values] = atof(next);
			n_values++;
		}
		return strlen(buffer);
	}
	else
	{
		// write data to buffer
		size_t sz = 0;
		for ( int n = 0 ; n < n_values && sz < len ; n++ )
		{
			sz += snprintf(buffer+sz,len-sz+1,"%s%g",sz>0?",":"",values[n]);
		}
		return sz;
	}
}

int system::p(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// get size of output buffer needed
		len = 0;
		for ( int n = 0 ; n < n_values ; n++ )
		{
			int sz = snprintf(NULL,0,"%g",probs[n]);
			if ( sz < 0 )
			{
				return -1;
			}
			len += sz + 1;
		}
		return len;
	}
	else if ( len == 0 )
	{
		// read data from buffer
		char *next=NULL, *last=NULL;
		int n = 0;
		while ( (next=strtok_r(next?NULL:buffer,",",&last)) != NULL )
		{
			if ( n < n_values )
			{
				probs[n++] = atof(next);
			}
			else
			{
				error("too many probabilities for %d states",n);
				return -1;
			}
		}
		return strlen(buffer);
	}
	else
	{
		// write data to buffer
		size_t sz = 0;
		for ( int n = 0 ; n < n_values && sz < len ; n++ )
		{
			sz += snprintf(buffer+sz,len-sz+1,"%s%g",sz>0?",":"",probs[n]);
		}
		return sz;
	}
}

int system::device(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		return point_names ? strlen(point_names) : 0;
	}
	else if ( len == 0 )
	{
		// read data from buffer
		if ( n_points == max_points )
		{
			max_points *= 2;
			point_list = (gld_property**)realloc(point_list,max_points);
			name_list = (char**)realloc(name_list,max_points);
		}
		point_list[n_points] = new gld_property(buffer);
		name_list[n_points] = strdup(buffer);
		if ( point_list[n_points] == NULL || name_list[n_points] == NULL )
		{
			error("memory allocation failure");
			return 0;
		}
		if ( point_list[n_points]->get_type() != PT_double && point_list[n_points]->get_type() != PT_enumeration )
		{
			error("target point is not a double or enumeration value");
			return 0;
		}
		n_points++;

		// copy name to list of names
		int pos = strlen(point_names);
		len = strlen(buffer);
		point_names = (char*)realloc(point_names,pos+len+3);
		snprintf(point_names+pos,len+2,"%s%s",pos>0?",":"",buffer);
		return len;
	}
	else
	{
		return snprintf(buffer,len-1,"%s",point_names);
	}
}
