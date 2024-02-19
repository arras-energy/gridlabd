// module/pypower/bus.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(bus);
EXPORT_INIT(bus);
EXPORT_COMMIT(bus);

CLASS *bus::oclass = NULL;
bus *bus::defaults = NULL;

bus::bus(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"bus",sizeof(bus),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class bus";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,
			PT_int32, "bus_i", get_bus_i_offset(),

			PT_enumeration, "type", get_type_offset(),
				PT_KEYWORD, "UNKNOWN", (enumeration)0,
				PT_KEYWORD, "PQ", (enumeration)1,
				PT_KEYWORD, "PV", (enumeration)2,
				PT_KEYWORD, "REF", (enumeration)3,
				PT_KEYWORD, "NONE", (enumeration)4,

			PT_double, "Pd[MW]", get_Pd_offset(),

			PT_double, "Qd[MVar]", get_Qd_offset(),

			PT_double, "Gs[MW]", get_Gs_offset(),

			PT_double, "Bs[MVar]", get_Bs_offset(),

			PT_int32, "area", get_area_offset(),

			PT_double, "base_kV[kV]", get_base_kV_offset(),

			PT_double, "Vm[pu*V]", get_Vm_offset(),

			PT_double, "Va[deg]", get_Va_offset(),

			PT_int, "zone", get_zone_offset(),

			PT_double, "Vmax", get_Vmax_offset(),

			PT_double, "Vmin", get_Vmin_offset(),

			NULL)<1){
				char msg[256];
				snprintf(msg,sizeof(msg)-1, "unable to publish properties in %s",__FILE__);
				throw msg;
		}
	}
}

int bus::create(void) 
{
	return 1; /* return 1 on success, 0 on failure */
}

int bus::init(OBJECT *parent)
{
	return 1;
}

TIMESTAMP bus::commit(TIMESTAMP t1, TIMESTAMP t2)
{
	return TS_NEVER;
}
