// module/pypower/powerplant.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_POWERPLANT_H
#define _PYPOWER_POWERPLANT_H

#include "gridlabd.h"

class powerplant : public gld_object
{

public:

	typedef enum {
		GT_UNDEFINED 			= 0x0000,
		GT_UNKNOWN 				= 0x0001,
		GT_HYDROTURBINE 		= 0x0002,
		GT_STEAMTURBINE			= 0x0004,
		GT_COMPRESSEDAIR		= 0x0008,
		GT_INTERNALCOMBUSTION 	= 0x0010,
		GT_FLYWHEEL				= 0x0020,
		GT_WINDTURBINE			= 0x0040,
		GT_ENERGYSTORAGE		= 0x0080,
		GT_COMBUSTIONTURBINE 	= 0x0100,
		GT_PHOTOVOLTAIC			= 0x0200,
		GT_COMBINEDCYCLE		= 0x0400,
	} GENERATORTYPE;

	typedef enum {
		FT_UNDEFINED	= 0x00000000,
		FT_ELECTRICITY 	= 0x00000001, 
		FT_WIND 		= 0x00000002,
		FT_SOLAR		= 0x00000004, 
		FT_GEOTHERMAL 	= 0x00000008, 
		FT_COKE 		= 0x00000010, 
		FT_WASTE 		= 0x00000020, 
		FT_BIOMASS 		= 0x00000040, 
		FT_OIL 			= 0x00000080, 
		FT_UNKNOWN 		= 0x00000100, 
		FT_WOOD 		= 0x00000200, 
		FT_OTHER 		= 0x00000400, 
		FT_GAS 			= 0x00000800, 
		FT_NUCLEAR 		= 0x00001000, 
		FT_WATER 		= 0x00002000,
		FT_COAL 		= 0x00004000, 
		FT_NATURALGAS 	= 0x00008000, 
	} FUELTYPE;

	typedef enum {
		GS_OFFLINE = 0,
		GS_ONLINE = 1,
	} GENERATORSTATUS;

public:
	// published properties
	GL_ATOMIC(char32,city);
	GL_ATOMIC(char32,state);
	GL_ATOMIC(char32,zipcode);
	GL_ATOMIC(char32,country);
	GL_ATOMIC(char32,naics_code);
	GL_ATOMIC(char256,naics_description);
	GL_ATOMIC(char32,plant_code);
	GL_ATOMIC(set,generator);
	GL_ATOMIC(set,fuel);
	GL_ATOMIC(enumeration,status)
	GL_ATOMIC(double,operating_capacity);
	GL_ATOMIC(double,summer_capacity);
	GL_ATOMIC(double,winter_capacity);
	GL_ATOMIC(double,capacity_factor);
	GL_ATOMIC(char256,substation_1);
	GL_ATOMIC(char256,substation_2);
	GL_ATOMIC(double,storage_capacity);
	GL_ATOMIC(double,charging_capacity);
	GL_ATOMIC(double,storage_efficiency);
	GL_ATOMIC(double,state_of_charge);
	GL_ATOMIC(complex,S);
	GL_ATOMIC(char256,controller);
	GL_ATOMIC(double,startup_cost);
	GL_ATOMIC(double,shutdown_cost);
	GL_ATOMIC(double,fixed_cost);
	GL_ATOMIC(double,variable_cost);
	GL_ATOMIC(double,scarcity_cost);
	GL_ATOMIC(double,energy_rate);
	GL_ATOMIC(double,ramp_rate);
	GL_ATOMIC(double,total_cost);
	GL_ATOMIC(double,emissions_rate);
	GL_ATOMIC(double,total_emissions);
	GL_ATOMIC(double,Pg);
	GL_ATOMIC(double,Qg);

private:
	PyObject *py_controller;
	PyObject *py_args;
	PyObject *py_kwargs;

private:
	bool is_dynamic; // true if parent is a gen otherwise false
	TIMESTAMP last_t;
	gencost *costobj;
	double last_Sm;
	double delta_t;
	double gen_cf; // gen contribution factor

public:
	// event handlers
	powerplant(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);
	TIMESTAMP presync(TIMESTAMP t0);
	TIMESTAMP sync(TIMESTAMP t0);
	TIMESTAMP postsync(TIMESTAMP t0);
	TIMESTAMP commit(TIMESTAMP t0, TIMESTAMP t1);

public:
	// internal properties
	static CLASS *oclass;
	static powerplant *defaults;
};

#endif // _LOAD_H
