// module/pypower/scada.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_SCADA_H
#define _PYPOWER_SCADA_H

#include "gridlabd.h"

class scada : public gld_object 
{

public:
	// published properties
	GL_ATOMIC(complex,V);
	GL_ATOMIC(double,Vm);
	GL_ATOMIC(double,Va);
	GL_ATOMIC(complex,I);
	GL_ATOMIC(complex,S);

private:
	bool parent_is_branch;

public:

	// event handlers
	scada(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP presync(TIMESTAMP t0);
	TIMESTAMP sync(TIMESTAMP t0);
	TIMESTAMP postsync(TIMESTAMP t0);

public:
	// internal properties
	static CLASS *oclass;
	static scada *defaults;
};

#endif // _BUS_H
