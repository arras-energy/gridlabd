// module/pypower/gencost.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(gencost);
EXPORT_INIT(gencost);

CLASS *gencost::oclass = NULL;
gencost *gencost::defaults = NULL;

gencost::gencost(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"gencost",sizeof(gencost),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class gencost";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,
			PT_enumeration, "model", get_model_offset(),
				PT_DESCRIPTION, "cost model (1=piecewise linear, 2=polynomial)",
				PT_KEYWORD, "UNKNOWN", (enumeration)CM_UNKNOWN,
				PT_KEYWORD, "PIECEWISE", (enumeration)CM_PIECEWISE,
				PT_KEYWORD, "POLYNOMIAL", (enumeration)CM_POLYNOMIAL,

			PT_double, "startup[$]", get_startup_offset(),
				PT_DESCRIPTION, "startup cost ($)",

			PT_double, "shutdown[$]", get_shutdown_offset(),
				PT_DESCRIPTION, "shutdown cost($)",

			PT_char1024, "costs", get_costs_offset(),
				PT_DESCRIPTION, "cost model (comma-separate values)",

			NULL)<1)
		{
				throw "unable to publish properties in pypower gencost";
		}
	}
}

int gencost::create(void) 
{
	set_model(CM_UNKNOWN);
	set_startup(0.0);
	set_shutdown(0.0);
	set_costs("");

	index = 0;

	extern gencost *gencostlist[MAXENT];
	extern size_t ngencost;
	if ( ngencost < MAXENT )
	{
		index = ngencost++;
		gencostlist[index] = this;
	}
	else
	{
		throw "maximum gencost entities exceeded";
	}

	return 1; /* return 1 on success, 0 on failure */
}

int gencost::init(OBJECT *parent)
{
	while ( parent != NULL && ! get_object(parent)->isa("gen","pypower") )
	{
		parent = parent->parent;
	}
	if ( parent == NULL )
	{
		error("parent does not trace back to a pypower.gen object");
		return 0;
	}
	OBJECTDATA(parent,gen)->add_cost(this);

	if ( model == CM_UNKNOWN )
	{
		error("cost model must be PIECEWISE or POLYNOMIAL");
		return 0;
	}

	if ( startup < 0 )
	{
		error("startup cost must be non-negative");
		return 0;
	}

	if ( shutdown < 0 )
	{
		error("shutdown cost must be non-negative");
		return 0;
	}
	
	return 1;
}

bool gencost::is_equal(gencost *other)
{
	if ( other->get_model() != model )
	{
		return false;
	}
	if ( other->get_startup() != startup )
	{
		return false;
	}
	if ( other->get_shutdown() != shutdown )
	{
		return false;
	}
	return strcmp(other->get_costs(),costs) == 0 ? true : false;
}

