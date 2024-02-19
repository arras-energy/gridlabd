// module/pypower/bus.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _BUS_H
#define _BUS_H

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
	GL_ATOMIC(double,base_kV);
	GL_ATOMIC(int32,zone);
	GL_ATOMIC(double,Vmax);
	GL_ATOMIC(double,Vmin);

public:
	// event handlers
	bus(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP commit(TIMESTAMP t1, TIMESTAMP t2);

public:
	// internal properties
	static CLASS *oclass;
	static bus *defaults;
};

#endif // _BUS_H
