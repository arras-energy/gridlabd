// module/behavior/system.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "behavior.h"

EXPORT_CREATE(system);
EXPORT_INIT(system);
EXPORT_PRECOMMIT(system);
EXPORT_METHOD(system,u);
EXPORT_METHOD(system,p);
EXPORT_METHOD(system,q);
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

			PT_double, "tau", get_tau_offset(),
				PT_DESCRIPTION, "System activity",

			PT_double, "mu", get_mu_offset(),
				PT_DESCRIPTION, "Asset potential",

			PT_int64, "N", get_N_offset(),
				PT_DESCRIPTION, "Number of devices",

			PT_int64, "N0", get_N0_offset(),
				PT_DESCRIPTION, "Number of sites",

			PT_method, "u", get_u_offset(),
				PT_DESCRIPTION, "State values",

			PT_method, "q", get_q_offset(),
				PT_DESCRIPTION, "State quantities",

			PT_method, "device", get_device_offset(),
				PT_DESCRIPTION, "Property of device connected to this system",

			PT_double, "U", get_U_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Total value of all states",

			PT_double, "sigma", get_sigma_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "System entropy",

			PT_method, "p", get_p_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "State probabilities",

			PT_double, "Z", get_Z_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "State partition function",

			PT_double, "F", get_F_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Free value",

			PT_double, "P", get_P_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Internal price",

			PT_double, "Q", get_Q_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Total quantity",

			PT_double, "Nexp", get_Nexp_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Expected number of devices",

			PT_double, "Uexp", get_Uexp_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Expected device value",

			PT_double, "Qexp", get_Qexp_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Expected quantity",

			PT_double, "chi", get_chi_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Price susceptibility",

			PT_double, "Cp", get_Cp_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Value capacity",

			PT_object, "connection", get_connection_offset(),
				PT_DESCRIPTION, "Connection to another system",

			PT_enumeration, "connection_type", get_connection_type_offset(),
				PT_KEYWORD, "ASSET", (enumeration)ASSET,
				PT_KEYWORD, "VALUE", (enumeration)VALUE,
				PT_KEYWORD, "NONE", (enumeration)NONE,
				PT_DESCRIPTION, "Type of connection (tau or tau+mu)",

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
	n_states = 0;
	values = NULL;
	probs = NULL;
	quants = NULL;

	n_points = 0;
	max_points = 1024;
	point_list = (gld_property**)malloc(sizeof(gld_property*)*max_points);
	name_list = (char **)malloc(sizeof(char*)*max_points);
	point_names = (char*)malloc(1);
	point_names[0] = '\0';
	add_system(this);
	return 1; // return 1 on success, 0 on failure
}

int system::init(OBJECT *parent)
{
	if ( n_states < 2 )
	{
		error("there must be at least 2 state values u specified");
		return 0;
	}
	if ( connection != NULL && ! gl_object_isa(connection,"system","behavior") )
	{
		error("connection must be to another behavior system object");
		return 0;
	}
	update();
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

void system::update(void)
{
	Z = 0.0;
	Nexp = 0.0;
	Uexp = 0.0;
	sigma = 0.0;
	Qexp = 0.0;
	chi = 0.0;
	Cp = 0.0;
	double u_min = 0;
	bool zero_tau = ( fabs(tau) <= resolution );
	if ( ! zero_tau )
	{
		for ( int n = 0 ; n < n_states ; n++ )
		{
			double y = N*mu-values[n];
			double x = exp(y);
			if ( isfinite(x) && ! isnan(x) ) // && x >= resolution ) // && x < 1/resolution )
			{
				probs[n] = x;
				Cp += y*x;
				Z += x;
			}
			else
			{
				probs[n] = 0.0;
			}
		}
		// if ( fabs(Z) < resolution )
		// {
		// 	zero_tau = true;
		// 	Z = 0;
		// }
	}
	for ( int n = 0 ; n < n_states ; n++ )
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
			if ( x > 0 )
			{
				Nexp += N*x;
				Uexp += values[n]*x;
				Qexp += quants[n]*x;
			}
		}
	}
	if ( zero_tau )
	{
		for ( int n = 0 ; n < n_states ; n++ )
		{
			if ( fabs(values[n]-u_min) < resolution )
			{
				probs[n] = 1;
				Nexp += N;
				Uexp += values[n];
				Qexp += quants[n];
				Z++;
			}
		}
	}
	for ( int n = 0 ; n < n_states ; n++ )
	{
		probs[n] = round(probs[n]/Z/resolution)*resolution;
		if ( probs[n] > 0 )
		{
			sigma += -probs[n]*log(probs[n]);
		}
	}
	Nexp /= Z;
	Uexp /= Z;
	Qexp /= Z;
	if ( ! zero_tau )
	{
		if ( N > 0 )
		{
			chi = round(Qexp/(N*tau)/resolution)*resolution;
		}
		double tauZ = tau * Z;
		if ( fabs(tauZ) > resolution )
		{
			Cp = round(N * Uexp *Cp / (tauZ*tauZ) / resolution)*resolution;
		}
	}
	Nexp = round(Nexp/Z/resolution)*resolution;
	Uexp = round(Uexp/Z/resolution)*resolution;
	Qexp = round(Qexp/Z/resolution)*resolution;
	sigma = round(sigma/resolution)*resolution;
	if ( zero_tau )
	{
		Z = 0;
	}

	Q = n_points > 0 ? 0.0 : round(N*Qexp/resolution)*resolution;
	U = n_points > 0 ? 0.0 : round(N*Uexp/resolution)*resolution;
	for ( size_t n = 0 ; n < n_points ; n++ )
	{
		gld_property *prop = point_list[n];
		double r = gl_random_uniform(&(prop->get_object()->rng_state),0,1);
		double rs = 0.0;
		int s;
		for ( s = 0 ; s < n_states ; s++ )
		{
			rs += probs[s];
			if ( r <= rs )
			{
				break;
			}
		}
		if ( s == n_states )
		{
			s = n_states - 1;
		}
		Q += quants[s];
		U += values[s];
		switch ( prop->get_type() )
		{
		case PT_enumeration:
			prop->setp(s);
			break;
		case PT_double:
			prop->setp(quants[s]);
			break;
		default:
			break;
		}
	}
	F = round((U-tau*sigma)/resolution)*resolution;
	P = ( Q != 0.0 ? round(-U/Q/resolution)*resolution : 0.0);
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
		for ( int n = 0 ; n < n_states ; n++ )
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
			values = (double*)realloc(values,(n_states+1)*(sizeof(*values)));
			probs = (double*)realloc(probs,(n_states+1)*(sizeof(*values)));
			quants = (double*)realloc(quants,(n_states+1)*(sizeof(*values)));
			if ( values == NULL || probs == NULL )
			{
				exception("memory allocation error reallocating values buffer");
			}
			values[n_states] = atof(next);
			n_states++;
		}
		return strlen(buffer);
	}
	else
	{
		// write data to buffer
		size_t sz = 0;
		for ( int n = 0 ; n < n_states && sz < len ; n++ )
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
		for ( int n = 0 ; n < n_states ; n++ )
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
			if ( n < n_states )
			{
				probs[n++] = atof(next);
			}
			else
			{
				error("state %d does not have a defined value for probability %g",n,atof(next));
			}
		}
		return strlen(buffer);
	}
	else
	{
		// write data to buffer
		size_t sz = 0;
		for ( int n = 0 ; n < n_states && sz < len ; n++ )
		{
			sz += snprintf(buffer+sz,len-sz+1,"%s%g",sz>0?",":"",probs[n]);
		}
		return sz;
	}
}

int system::q(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// get size of output buffer needed
		len = 0;
		for ( int n = 0 ; n < n_states ; n++ )
		{
			int sz = snprintf(NULL,0,"%g",quants[n]);
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
			if ( n < n_states )
			{
				quants[n++] = atof(next);
			}
			else
			{
				error("state %d does not have a defined value for quantity %g",n,atof(next));
			}
		}
		return strlen(buffer);
	}
	else
	{
		// write data to buffer
		size_t sz = 0;
		for ( int n = 0 ; n < n_states && sz < len ; n++ )
		{
			sz += snprintf(buffer+sz,len-sz+1,"%s%g",sz>0?",":"",quants[n]);
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
