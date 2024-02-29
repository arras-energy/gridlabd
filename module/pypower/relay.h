// module/pypower/relay.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_RELAY_H
#define _PYPOWER_RELAY_H

#include "gridlabd.h"

class relay : public gld_object
{

public:
	// published properties
	GL_ATOMIC(complex,impedance);
	GL_ATOMIC(double,rating);
	typedef enum {RS_OUT=0,RS_IN=1} RELAYSTATUS;
	GL_ATOMIC(enumeration,status);

public:
	GL_ATOMIC(complex,Z);
	GL_ATOMIC(complex,Y);

public:
	bool parent_is_branch;

public:
	// event handlers
	relay(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static relay *defaults;
};

#endif // _LOAD_H
