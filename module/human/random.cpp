// module/human/random.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "human.h"

EXPORT_CREATE(random);
EXPORT_INIT(random);
EXPORT_PRECOMMIT(random);
EXPORT_METHOD(random,point);

CLASS *random::oclass = NULL;
class random *random::defaults = NULL;

int32 random::limit_retries = 1000;

random::random(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"random",sizeof(random),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class random";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_enumeration, "type", get_type_offset(),
				PT_KEYWORD, "DEGENERATE", (enumeration)RT_DEGENERATE,
				PT_KEYWORD, "UNIFORM", (enumeration)RT_UNIFORM,
				PT_KEYWORD, "NORMAL", (enumeration)RT_NORMAL,
				PT_KEYWORD, "LOGNORMAL", (enumeration)RT_LOGNORMAL,
				PT_KEYWORD, "BERNOULLI", (enumeration)RT_BERNOULLI,
				PT_KEYWORD, "PARETO", (enumeration)RT_PARETO,
				PT_KEYWORD, "EXPONENTIAL", (enumeration)RT_EXPONENTIAL,
				PT_KEYWORD, "RAYLEIGH", (enumeration)RT_RAYLEIGH,
				PT_KEYWORD, "RT_WEIBULL", (enumeration)RT_WEIBULL,
				PT_KEYWORD, "RT_GAMMA", (enumeration)RT_GAMMA,
				PT_KEYWORD, "RT_BETA", (enumeration)RT_BETA,
				PT_KEYWORD, "RT_TRIANGLE", (enumeration)RT_TRIANGLE,
				PT_DESCRIPTION, "Distribution type to be used to generate values",

			PT_double, "a", get_a_offset(),
				PT_DESCRIPTION, "The first distribution parameter value",

			PT_double, "b", get_b_offset(),
				PT_DESCRIPTION, "The second distribution parameter value",

			PT_double, "lower_limit", get_lower_limit_offset(),
				PT_DESCRIPTION, "The lower limit for generated values",

			PT_double, "upper_limit", get_upper_limit_offset(),
				PT_DESCRIPTION, "The upper limit for generated values",

			PT_enumeration, "limit_method", get_limit_method_offset(),
				PT_KEYWORD, "CLAMP", (enumeration)LM_CLAMP,
				PT_KEYWORD, "RETRY", (enumeration)LM_RETRY,
				PT_DESCRIPTION, "Method to use to enforce limits",

			PT_double, "refresh_rate[s]", get_refresh_rate_offset(),
				PT_DESCRIPTION, "The rate at which values are generated",

			PT_method, "point", get_point_offset(),
				PT_DESCRIPTION, "Point to which random value is posted as <object-name>:<property-name>",

			NULL)<1)
		{
				throw "unable to publish random properties";
		}
	}
}

int random::create(void) 
{
	n_points = 0;
	max_points = 1024;
	point_list = (gld_property**)malloc(sizeof(gld_property*)*max_points);
	name_list = (char **)malloc(sizeof(char*)*max_points);
	point_names = (char*)malloc(1);
	point_names[0] = '\0';
	return 1; // return 1 on success, 0 on failure
}

int random::init(OBJECT *parent)
{
	if ( get_lower_limit() > get_upper_limit() )
	{
		warning("lower limit is equal to upper limit");
	}
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP random::precommit(TIMESTAMP t0)
{
	TIMESTAMP t1 = TS_NEVER;
	for ( size_t n = 0 ; n < n_points ; n++ )
	{
		int retry = 0;
		unsigned int *state = &(my()->rng_state);
Retry:
		double x = gl_pseudorandomvalue((RANDOMTYPE)get_type(),state,a,b);
		if ( limit_method == LM_CLAMP )
		{
			x = min(upper_limit,max(lower_limit,x));
		}
		else if ( x < lower_limit || x > upper_limit )
		{
			retry++;
			if ( retry < limit_retries )
			{
				goto Retry;
			}
			else
			{
				warning("RETRY limit reached, return the CLAMP result instead");
				x = min(upper_limit,max(lower_limit,x));
			}
		}
		point_list[n]->setp(x);
	}
	if ( get_refresh_rate() > 0 )
	{
		t1 = (TIMESTAMP)((long(t0/get_refresh_rate()) + 1)*get_refresh_rate());
	}
	return t1;
}

int random::point(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		return strlen(point_names);
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
		if ( point_list[n_points]->get_type() != PT_double )
		{
			error("target point is not a double-type value");
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
