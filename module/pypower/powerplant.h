// module/pypower/powerplant.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_POWERPLANT_H
#define _PYPOWER_POWERPLANT_H

#include "gridlabd.h"

class powerplant : public gld_object
{

public:
	// published properties
	GL_ATOMIC(char32,city);
	GL_ATOMIC(char32,state);
	GL_ATOMIC(char32,zipcode);
	GL_ATOMIC(char32,country);
	GL_ATOMIC(char32,naics_code);
	GL_ATOMIC(char256,naics_description);
	GL_ATOMIC(int16,plant_code);
	GL_ATOMIC(set,generator);
	GL_ATOMIC(set,fuel);
	GL_ATOMIC(enumeration,status)
	GL_ATOMIC(double,operating_capacity);
	GL_ATOMIC(double,summer_capacity);
	GL_ATOMIC(double,winter_capacity);
	GL_ATOMIC(double,capacity_factor);
	GL_ATOMIC(char256,substation_1);
	GL_ATOMIC(char256,substation_2);
	GL_ATOMIC(complex,S);
	GL_ATOMIC(char256,controller);

private:
	PyObject *py_controller;
	PyObject *py_args;
	PyObject *py_kwargs;

private:
	bool is_dynamic; // true if parent is a gen otherwise false

public:
	// event handlers
	powerplant(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP presync(TIMESTAMP t1);
	TIMESTAMP sync(TIMESTAMP t1);
	TIMESTAMP postsync(TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static powerplant *defaults;
};

#endif // _LOAD_H
