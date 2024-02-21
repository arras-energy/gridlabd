// module/pypower/load.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _LOAD_H
#define _LOAD_H

#include "gridlabd.h"

class load : public gld_object 
{

public:
	// published properties
	GL_ATOMIC(complex,S);
	GL_ATOMIC(complex,Z)
	GL_ATOMIC(complex,I);
	GL_ATOMIC(complex,P);
	GL_ATOMIC(complex,V);
	GL_ATOMIC(double,Vn);

public:
	// event handlers
	load(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP commit(TIMESTAMP t1, TIMESTAMP t2);

public:
	// internal properties
	static CLASS *oclass;
	static load *defaults;
};

#endif // _LOAD_H
