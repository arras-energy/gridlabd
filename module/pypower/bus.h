// module/pypower/bus.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_BUS_H
#define _PYPOWER_BUS_H

#include "gridlabd.h"

class bus : public gld_object 
{
public:

	static char256 timestamp_format;

public:
	typedef struct s_sensitivity
	{
		double *value; 
		double *source;
		double slope;
		char cutoff_test;
		double cutoff_value;
		struct s_sensitivity *next;
	} SENSITIVITY;

public:
	// published properties
	GL_ATOMIC(int32,bus_i);
	GL_ATOMIC(enumeration,type);
	GL_ATOMIC(double,Pd);
	GL_ATOMIC(double,Qd);
	GL_ATOMIC(double,Gs);
	GL_ATOMIC(double,Bs);
	GL_ATOMIC(int32,area);
	GL_ATOMIC(double,baseKV);
	GL_ATOMIC(double,Vm);
	GL_ATOMIC(double,Va);
	GL_ATOMIC(int32,zone);
	GL_ATOMIC(double,Vmax);
	GL_ATOMIC(double,Vmin);
	GL_ATOMIC(double,lam_P);
	GL_ATOMIC(double,lam_Q);
	GL_ATOMIC(double,mu_Vmax);
	GL_ATOMIC(double,mu_Vmin);
	GL_ATOMIC(complex,S);
	GL_ATOMIC(char1024,weather_file);
	GL_ATOMIC(char1024,weather_variables);
	GL_ATOMIC(double,weather_resolution);

	GL_ATOMIC(double,Sh);
	GL_ATOMIC(double,Sn);
	GL_ATOMIC(double,Sg);
	GL_ATOMIC(double,Wd);
	GL_ATOMIC(double,Ws);
	GL_ATOMIC(double,Td);
	GL_ATOMIC(double,Tw);
	GL_ATOMIC(double,RH);
	GL_ATOMIC(double,PW);
	GL_ATOMIC(double,HI);
#define N_WEATHERDATA 10 // adjust if adding more weather data items

	GL_ATOMIC(char1024,weather_sensitivity);

private:

	bool load_weather(void);
	bool add_weather(TIMESTAMP t,char *buffer);
	bool get_weather(TIMESTAMP t);

	typedef struct s_weatherdata {
		TIMESTAMP t;
		double value[N_WEATHERDATA];
		struct s_weatherdata *next;
	} WEATHERDATA;
	gld_property *weather_mapper[N_WEATHERDATA];
	WEATHERDATA *first, *last, *current;

	SENSITIVITY *sensitivity_list;
	complex DS;

public:
	
	complex V;

public:

	// event handlers
	bus(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP presync(TIMESTAMP t0);
	TIMESTAMP sync(TIMESTAMP t0);
	TIMESTAMP postsync(TIMESTAMP t0);
	TIMESTAMP precommit(TIMESTAMP t0);

public:
	// internal properties
	static CLASS *oclass;
	static bus *defaults;
};

#endif // _BUS_H
