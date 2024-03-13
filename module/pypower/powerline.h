// module/pypower/powerline.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_POWERLINE_H
#define _PYPOWER_POWERLINE_H

#include "gridlabd.h"

class powerline : public gld_object
{

public:
	// published properties
	GL_ATOMIC(double,length);
	GL_ATOMIC(complex,impedance);
	GL_ATOMIC(double,rating);
	typedef enum {PLS_OUT=0,PLS_IN=1} POWERLINESTATUS;
	GL_ATOMIC(enumeration,status);
	typedef enum {PLC_SERIES=1,PLC_PARALLEL=2} POWERLINECOMPOSITION;
	GL_ATOMIC(enumeration,composition);

public:
	GL_ATOMIC(double,ratio);
	GL_ATOMIC(double,angle);
	GL_ATOMIC(double,rateA);
	GL_ATOMIC(complex,Z);
	GL_ATOMIC(complex,Y);

public:
	bool parent_is_branch;

public:
	// event handlers
	powerline(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static powerline *defaults;
};

#endif // _LOAD_H
