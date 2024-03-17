// module/pypower/relay.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_RELAY_H
#define _PYPOWER_RELAY_H

#include "gridlabd.h"

class relay : public gld_object
{

public:
	// published properties
	GL_ATOMIC(char256,controller);
	typedef enum {RS_CLOSED=0,RS_OPEN=1} RELAYSTATUS;
	GL_ATOMIC(enumeration,status);

private:
	PyObject *py_controller;
	PyObject *py_args;
	PyObject *py_kwargs;

public:
	// event handlers
	relay(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP presync(TIMESTAMP t1) { return TS_NEVER;};
	TIMESTAMP sync(TIMESTAMP t1);
	TIMESTAMP postsync(TIMESTAMP t1) { return TS_NEVER;};

public:
	// internal properties
	static CLASS *oclass;
	static relay *defaults;
};

#endif // _LOAD_H
