// module/pypower/transformer.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_TRANSFORMER_H
#define _PYPOWER_TRANSFORMER_H

#include "gridlabd.h"

class transformer : public gld_object
{

public:
	// published properties
	GL_ATOMIC(double,turns_ratio);
	GL_ATOMIC(double,phase_shift);
	GL_ATOMIC(complex,impedance);
	GL_ATOMIC(double,rating);
	typedef enum {TS_OUT=0,TS_IN=1} TRANSFORMERSTATUS;
	GL_ATOMIC(enumeration,status);

public:
	bool parent_is_branch;

public:
	// event handlers
	transformer(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static transformer *defaults;
};

#endif // _LOAD_H
