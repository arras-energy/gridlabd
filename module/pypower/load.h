// module/pypower/load.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_LOAD_H
#define _PYPOWER_LOAD_H

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
	typedef enum {LS_OFFLINE=0, LS_ONLINE=1, LS_CURTAILED=2,} LOADSTATUS;
	GL_ATOMIC(enumeration,status);
	GL_ATOMIC(double,response);
	GL_ATOMIC(char256,controller);

private:
	PyObject *py_controller;
	PyObject *py_args;
	PyObject *py_kwargs;

public:
	// event handlers
	load(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP presync(TIMESTAMP t1);
	TIMESTAMP sync(TIMESTAMP t1);
	TIMESTAMP postsync(TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static load *defaults;
};

#endif // _LOAD_H
