// module/human/random.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "human.h"

EXPORT_CREATE(random);
EXPORT_INIT(random);

CLASS *random::oclass = NULL;
random *random::defaults = NULL;

static int last_i = 0;

random::random(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"random",sizeof(random),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class random";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			NULL)<1)
		{
				throw "unable to publish random properties";
		}
	}
}

int random::create(void) 
{
	return 1; // return 1 on success, 0 on failure
}

int random::init(OBJECT *parent)
{
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}
