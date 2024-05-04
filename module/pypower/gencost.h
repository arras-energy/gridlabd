// module/pypower/gencost.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_GENCOST_H
#define _PYPOWER_GENCOST_H

#include "gridlabd.h"

class gencost : public gld_object 
{
private:
	typedef enum {CM_UNKNOWN=0,CM_PIECEWISE=1,CM_POLYNOMIAL} COSTMODEL;

public:
	// published properties
	GL_ATOMIC(enumeration,model);
	GL_ATOMIC(double,startup);
	GL_ATOMIC(double,shutdown);
	GL_ATOMIC(char1024,costs);

public:

	unsigned int index; // index into gencostlist
	
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
