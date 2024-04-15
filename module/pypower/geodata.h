// module/pypower/geodata.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_GEODATA_H
#define _PYPOWER_GEODATA_H

#include "gridlabd.h"

class geodata : public gld_object 
{

public:

	// typedefs
	typedef struct s_geodata
	{
		TIMESTAMP timestamp;
		double *value; // size is n_locations
	} GEODATA;
	typedef struct s_geocode
	{
		char hash[16];
		double latitude;
		double longitude;
		double **values;
		size_t max_values; // size of values
		size_t n_values; // last value
	} GEOCODE;

public:

	// published properties
	GL_ATOMIC(char1024,file);
	GL_ATOMIC(char256,target);

public:

	// public methods
	size_t find_location(const char *geocode,bool exact=false);
	size_t find_location(double lat, double lon);
	double get_value(size_t location);

private:

	// private data
	GEOCODE *locations;
	size_t n_locations; // size of locations and values
	GEODATA *data;
	size_t n_data; // size of data
	size_t cur_data; // index into data

private:

	// private methods
	bool add_target(OBJECT *obj,const char *propname);
	bool load_geodata(const char *file);
	bool set_time(TIMESTAMP timestamp);
	TIMESTAMP get_time();
	
public:

	// event handlers
	geodata(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);

public:

	// internal properties
	static CLASS *oclass;
	static geodata *defaults;
};

#endif // _PYPOWER_GEODATA_H
