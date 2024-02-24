// module/pypower/bus.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_BUS_H
#define _PYPOWER_BUS_H

#include "gridlabd.h"

class bus : public gld_object 
{

public:
	// published properties
	GL_ATOMIC(int32,bus_i);
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
	GL_ATOMIC(complex,total_load);

public:

	// event handlers
	bus(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);

public:
	// internal properties
	static CLASS *oclass;
	static bus *defaults;
};

#endif // _BUS_H
