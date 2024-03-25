// module/human/random.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _HUMAN_RANDOM_H
#define _HUMAN_RANDOM_H

#include "gridlabd.h"

DECL_METHOD(random,point);

class random : public gld_object 
{
public:

	static int32 limit_retries;

public:
	// published properties
	GL_ATOMIC(enumeration,type);
	GL_ATOMIC(double,a);
	GL_ATOMIC(double,b);
	GL_ATOMIC(double,lower_limit);
	GL_ATOMIC(double,upper_limit);
	typedef enum {
		LM_NONE = 0,
		LM_CLAMP = 1,
		LM_RETRY = 2,
	} LIMITMETHOD;
	GL_ATOMIC(enumeration,limit_method);
	GL_ATOMIC(double,refresh_rate);
	GL_METHOD(random,point);

private:

	gld_property **point_list;
	char **name_list;
	size_t n_points;
	size_t max_points;
	char *point_names;

public:

	// event handlers
	random(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);

public:
	// internal properties
	static CLASS *oclass;
	static random *defaults;
};

#endif // _HUMAN_RANDOM_H
