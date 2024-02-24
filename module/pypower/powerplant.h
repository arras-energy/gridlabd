// module/pypower/powerplant.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_POWERPLANT_H
#define _PYPOWER_POWERPLANT_H

#include "gridlabd.h"

class powerplant : public gld_object
{

public:
	// published properties
	GL_STRING(char32,city);
	GL_STRING(char32,state);
	GL_STRING(char32,zipcode);
	GL_STRING(char32,country);
	GL_STRING(char32,naics_code);
	GL_STRING(char256,naics_description);
	GL_ATOMIC(enumeration,plant_type);
	GL_ATOMIC(enumeration,status)
	GL_ATOMIC(int32,plant_code);
	GL_ATOMIC(double,operating_capacity);
	GL_ATOMIC(double,summer_capacity);
	GL_ATOMIC(double,winter_capacity);
	GL_ATOMIC(double,capacity_factor);
	GL_ATOMIC(enumeration,primary_fuel);
	GL_ATOMIC(enumeration,secondary_fuel);
	GL_ATOMIC(object,substation_1);
	GL_ATOMIC(object,substation_2);

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
