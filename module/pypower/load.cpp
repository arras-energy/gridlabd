// module/pypower/load.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(load);
EXPORT_INIT(load);
EXPORT_COMMIT(load);

CLASS *load::oclass = NULL;
load *load::defaults = NULL;

load::load(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"load",sizeof(load),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class load";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_complex, "S[VA]", get_S_offset(),
				PT_DESCRIPTION, "complex power demand (VA)",

			PT_complex, "V[V]", get_V_offset(),
				PT_DESCRIPTION, "complex voltage (V)",

			NULL) < 1 )
		{
				char msg[256];
				snprintf(msg,sizeof(msg)-1, "unable to publish properties in %s",__FILE__);
				throw msg;
		}
	}
}

int load::create(void) 
{
	extern load *loadlist[MAXENT];
	extern size_t nload;
	if ( nload < MAXENT )
	{
		loadlist[nload++] = this;
	}
	else
	{
		throw "maximum load entities exceeded";
	}

	return 1; /* return 1 on success, 0 on failure */
}

int load::init(OBJECT *parent)
{
	return 1;
}

TIMESTAMP load::commit(TIMESTAMP t1, TIMESTAMP t2)
{
	return TS_NEVER;
}
