// module/pypower/scada.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_SCADA_H
#define _PYPOWER_SCADA_H

#include "gridlabd.h"

DECL_METHOD(scada,point);

class scada : public gld_object 
{

public:

	// published properties
	GL_ATOMIC(bool,write_ok);
	GL_ATOMIC(bool,record_on);
	// typedef enum {DF_RAW,DF_STRING} DATAFORMAT;
	// GL_ATOMIC(enumeration,dataformat);
	GL_METHOD(scada,point);

public:

	// python controller function
	PyObject *py_controller;
	PyObject *py_scada;
	PyObject *py_historian;

	// property list
	gld_property **point_list;
	char **name_list;
	size_t n_points;
	size_t max_points;
	char *point_names;

public:

	// event handlers
	scada(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);
	TIMESTAMP commit(TIMESTAMP t0, TIMESTAMP t1);

public:

	// internal properties
	static CLASS *oclass;
	static scada *defaults;
};

#endif // _BUS_H
