// module/pypower/gen.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_GEN_H
#define _PYPOWER_GEN_H

#include "gridlabd.h"

class gen : public gld_object 
{

public:
	// published properties
	GL_ATOMIC(int32,bus);
	GL_ATOMIC(double,Pg);
	GL_ATOMIC(double,Qg);
	GL_ATOMIC(double,Qmax);
	GL_ATOMIC(double,Qmin);
	GL_ATOMIC(double,Vg);
	GL_ATOMIC(double,mBase);
	GL_ATOMIC(enumeration,status);
	GL_ATOMIC(double,Pmax);
	GL_ATOMIC(double,Pmin);
	GL_ATOMIC(double,Pc1);
	GL_ATOMIC(double,Pc2);
	GL_ATOMIC(double,Qc1min);
	GL_ATOMIC(double,Qc1max);
	GL_ATOMIC(double,Qc2min);
	GL_ATOMIC(double,Qc2max);
	GL_ATOMIC(double,ramp_agc);
	GL_ATOMIC(double,ramp_10);
	GL_ATOMIC(double,ramp_30);
	GL_ATOMIC(double,ramp_q);
	GL_ATOMIC(double,apf);
	GL_ATOMIC(double,mu_Pmax);
	GL_ATOMIC(double,mu_Pmin);
	GL_ATOMIC(double,mu_Qmax);
	GL_ATOMIC(double,mu_Qmin);

public:
	// event handlers
	gen(MODULE *module);
	int create(void);
	int init(OBJECT *parent);

public:
	// internal properties
	static CLASS *oclass;
	static gen *defaults;
};

#endif // _gen_H
