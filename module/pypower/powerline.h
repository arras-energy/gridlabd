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
	GL_ATOMIC(double,susceptance);
	GL_ATOMIC(double,rating);
	typedef enum {PLS_OUT=0,PLS_IN=1} POWERLINESTATUS;
	GL_ATOMIC(enumeration,status);
	typedef enum {PLC_NONE=0,PLC_SERIES=1,PLC_PARALLEL=2} POWERLINECOMPOSITION;
	GL_ATOMIC(enumeration,composition);

public:
	GL_ATOMIC(double,ratio);
	GL_ATOMIC(double,angle);
	GL_ATOMIC(double,rateA);
	GL_ATOMIC(complex,Z);
	GL_ATOMIC(complex,Y);
	GL_ATOMIC(double,b);

public:
	bool parent_is_branch;

public:
	// event handlers
	powerline(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP presync(TIMESTAMP t1);
	TIMESTAMP sync(TIMESTAMP t1);
	TIMESTAMP postsync(TIMESTAMP t1) { return TS_NEVER; };

public:
	// internal properties
	static CLASS *oclass;
	static powerline *defaults;
};

#endif // _LOAD_H
