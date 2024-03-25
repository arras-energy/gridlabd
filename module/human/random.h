// module/human/random.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _HUMAN_RANDOM_H
#define _HUMAN_RANDOM_H

#include "gridlabd.h"

class random : public gld_object 
{

public:
	// published properties

public:

	// event handlers
	random(MODULE *module);
	int create(void);
	int init(OBJECT *parent);

public:
	// internal properties
	static CLASS *oclass;
	static random *defaults;
};

#endif // _HUMAN_RANDOM_H
