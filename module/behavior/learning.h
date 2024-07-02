// module/behavior/learning.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _BEHAVIOR_LEARNING_H
#define _BEHAVIOR_LEARNING_H

#include "gridlabd.h"

DECL_METHOD(learning,target);
DECL_METHOD(learning,policy);
DECL_METHOD(learning,reward);

class learning : public gld_object 
{

public:
	// published properties
	GL_METHOD(learning,target);
	GL_METHOD(learning,policy);
	GL_ATOMIC(double,exploration);
	GL_ATOMIC(double,discount);
	GL_ATOMIC(double,interval);
	GL_METHOD(learning,reward);

public:

	// event handlers
	learning(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);
	TIMESTAMP commit(TIMESTAMP t0, TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static learning *defaults;
};

#endif // _BEHAVIOR_LEARNING_H
