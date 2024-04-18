// module/pypower/weather.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_WEATHER_H
#define _PYPOWER_WEATHER_H

#include "gridlabd.h"

class weather : public gld_object 
{
public:

	static char256 timestamp_format;

public:
	GL_ATOMIC(char1024,file);
	GL_ATOMIC(char1024,variables);
	GL_ATOMIC(double,resolution);

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
// #define N_WEATHERDATA 10 // adjust if adding more weather data items

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

public:

	// event handlers
	weather(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);

public:
	// internal properties
	static CLASS *oclass;
	static weather *defaults;
};

#endif // _PYPOWER_WEATHER_H
