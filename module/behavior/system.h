// module/behavior/system.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _BEHAVIOR_SYSTEM_H
#define _BEHAVIOR_SYSTEM_H

#include "gridlabd.h"

DECL_METHOD(system,u);
DECL_METHOD(system,p);
DECL_METHOD(system,Z);
DECL_METHOD(system,device);

class system : public gld_object 
{

public:
	static double resolution;

public:

	// published properties
	GL_ATOMIC(double,sigma);
	GL_ATOMIC(double,tau);
	GL_ATOMIC(double,mu);
	GL_ATOMIC(double,N);
	GL_ATOMIC(double,Z);
	GL_ATOMIC(double,Navg);
	GL_ATOMIC(double,Uavg);
	GL_METHOD(system,u);
	GL_METHOD(system,p);
	GL_METHOD(system,device);

private:

	// internal variables
	double *values;
	double *probs;
	int n_values;

	gld_property **point_list;
	char **name_list;
	size_t n_points;
	size_t max_points;
	char *point_names;

private:

	// internal functions
	void update(void);

public:

	// event handlers
	system(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);

public:

	// internal properties
	static CLASS *oclass;
	static system *defaults;
};

#endif // _BEHAVIOR_SYSTEM_H