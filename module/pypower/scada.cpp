// module/pypower/scada.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(scada);
EXPORT_INIT(scada);
EXPORT_SYNC(scada);

CLASS *scada::oclass = NULL;
scada *scada::defaults = NULL;

scada::scada(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"scada",sizeof(scada),PC_POSTTOPDOWN|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class scada";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_complex,"V[V]",get_V_offset(),

			PT_double,"Vm[V]",get_Vm_offset(),
			
			PT_double,"Va[deg]",get_Va_offset(),
			
			PT_complex,"I",get_I_offset(),
			
			PT_complex,"S",get_S_offset(),
			
			PT_double,"P",PADDR(get_S().Re()),
			
			PT_double,"Q",PADDR(get_S().Re()),

			NULL) < 1 )
		{
				throw "unable to publish scada properties";
		}
	}
}

int scada::create(void) 
{
	parent_is_branch = false;
	return 1; // return 1 on success, 0 on failure
}

int scada::init(OBJECT *parent)
{
	if ( get_parent() == NULL )
	{
		warning("scada object without parent is ignored");
	}
	else if ( get_parent()->isa("branch","pypower") )
	{
		parent_is_branch = true;
	}
	else if ( get_parent()->isa("bus","pypower") )
	{
		parent_is_branch = false;
	}
	else
	{
		error("parent '%s' is not a pypower bus or branch",get_parent()->get_name());
		return 0;
	}

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP scada::presync(TIMESTAMP t0)
{
	exception("invalid presync event call");
	return TS_NEVER;
}

TIMESTAMP scada::sync(TIMESTAMP t0)
{
	exception("invalid sync event call");
	return TS_NEVER;
}

TIMESTAMP scada::postsync(TIMESTAMP t0)
{
	if ( parent_is_branch )
	{
		branch *parent = (branch*)get_parent();
		complex Z(parent->get_r(),parent->get_x());
		// bus *from = NULL
		// bus *to = NULL;
		// complex DeltaV(to->get_V()-from->get_V());
	}
	else
	{
		bus *parent = (bus*)get_parent();
		set_Vm(parent->get_Vm());
		set_Va(parent->get_Va());
		// get_S().SetPolar(Vm,Va,'d');
	}
	return TS_NEVER;
}

