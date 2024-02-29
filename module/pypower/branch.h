// module/pypower/branch.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_BRANCH_H
#define _PYPOWER_BRANCH_H

#include "gridlabd.h"

class branch : public gld_object 
{

public:
	// published properties
	GL_ATOMIC(int32,fbus);
	GL_ATOMIC(int32,tbus);
	GL_ATOMIC(double,r);
	GL_ATOMIC(double,x);
	GL_ATOMIC(double,b);
	GL_ATOMIC(double,rateA);
	GL_ATOMIC(double,rateB);
	GL_ATOMIC(double,rateC);
	GL_ATOMIC(double,ratio);
	GL_ATOMIC(double,angle);
	GL_ATOMIC(int32,status);
	GL_ATOMIC(double,angmin);
	GL_ATOMIC(double,angmax);

public:
	GL_ATOMIC(int32,child_count);
	
public:
	// event handlers
	branch(MODULE *module);
	int create(void);
	int init(OBJECT *parent);

public:
	// internal properties
	static CLASS *oclass;
	static branch *defaults;
};

#endif // _branch_H
