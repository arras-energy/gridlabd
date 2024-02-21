// module/pypower/gencost.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_GENCOST_H
#define _PYPOWER_GENCOST_H

#include "gridlabd.h"

class gencost : public gld_object 
{

public:
	// published properties
	GL_ATOMIC(int32,gencost_i);
	GL_ATOMIC(enumeration,type);
	GL_ATOMIC(double,Pd);
	GL_ATOMIC(double,Qd);
	GL_ATOMIC(double,Gs);
	GL_ATOMIC(double,Bs);
	GL_ATOMIC(int32,area);
	GL_ATOMIC(double,baseKV);
	GL_ATOMIC(double,Vm);
	GL_ATOMIC(double,Va);
	GL_ATOMIC(int32,zone);
	GL_ATOMIC(double,Vmax);
	GL_ATOMIC(double,Vmin);
	GL_ATOMIC(double,lam_P);
	GL_ATOMIC(double,lam_Q);
	GL_ATOMIC(double,mu_Vmax);
	GL_ATOMIC(double,mu_Vmin);

public:
	// event handlers
	gencost(MODULE *module);
	int create(void);
	int init(OBJECT *parent);

public:
	// internal properties
	static CLASS *oclass;
	static gencost *defaults;
};

#endif // _gencost_H
