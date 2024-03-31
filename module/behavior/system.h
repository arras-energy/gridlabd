// module/behavior/system.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _BEHAVIOR_SYSTEM_H
#define _BEHAVIOR_SYSTEM_H

#include "gridlabd.h"

DECL_METHOD(system,u);
DECL_METHOD(system,p);
DECL_METHOD(system,q);
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
	GL_ATOMIC(int64,N);
	GL_ATOMIC(int64,N0);
	GL_ATOMIC(double,U);
	GL_ATOMIC(double,Z);
	GL_ATOMIC(double,F);
	GL_ATOMIC(double,P);
	GL_ATOMIC(double,Q);
	GL_ATOMIC(double,Nexp);
	GL_ATOMIC(double,Uexp);
	GL_ATOMIC(double,Qexp);
	GL_ATOMIC(double,chi);
	GL_ATOMIC(double,Cp);
	GL_METHOD(system,u);
	GL_METHOD(system,p);
	GL_METHOD(system,q);
	GL_METHOD(system,device);

private:

	// internal variables
	double *values;
	double *probs;
	double *quants;
	int n_states;

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
