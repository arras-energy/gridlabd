// module/pypower/bus.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(bus);
EXPORT_INIT(bus);

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
				PT_DESCRIPTION, "bus number (1 to 29997)",

			PT_enumeration, "type", get_type_offset(),
				PT_DESCRIPTION, "bus type (1 = PQ, 2 = PV, 3 = ref, 4 = isolated)",
				PT_KEYWORD, "UNKNOWN", (enumeration)0,
				PT_KEYWORD, "PQ", (enumeration)1,
				PT_KEYWORD, "PV", (enumeration)2,
				PT_KEYWORD, "REF", (enumeration)3,
				PT_KEYWORD, "NONE", (enumeration)4,

			PT_double, "Pd[MW]", get_Pd_offset(),
				PT_DESCRIPTION, "real power demand (MW)",

			PT_double, "Qd[MVAr]", get_Qd_offset(),
				PT_DESCRIPTION, "reactive power demand (MVAr)",

			PT_double, "Gs[MW]", get_Gs_offset(),
				PT_DESCRIPTION, "shunt conductance (MW at V = 1.0 p.u.)",

			PT_double, "Bs[MVAr]", get_Bs_offset(),
				PT_DESCRIPTION, "shunt susceptance (MVAr at V = 1.0 p.u.)",

			PT_int32, "area", get_area_offset(),
				PT_DESCRIPTION, "area number, 1-100",

			PT_double, "baseKV[kV]", get_baseKV_offset(),
				PT_DESCRIPTION, "voltage magnitude (p.u.)",

			PT_double, "Vm[pu*V]", get_Vm_offset(),
				PT_DESCRIPTION, "voltage angle (degrees)",

			PT_double, "Va[deg]", get_Va_offset(),
				PT_DESCRIPTION, "base voltage (kV)",

			PT_int32, "zone", get_zone_offset(),
				PT_DESCRIPTION, "loss zone (1-999)",

			PT_double, "Vmax", get_Vmax_offset(),
				PT_DESCRIPTION, "maximum voltage magnitude (p.u.)",

			PT_double, "Vmin", get_Vmin_offset(),
				PT_DESCRIPTION, "minimum voltage magnitude (p.u.)",

			PT_double, "lam_P", get_lam_P_offset(),
				PT_DESCRIPTION, "Lagrange multiplier on real power mismatch (u/MW)",
				PT_ACCESS, PA_REFERENCE,

			PT_double, "lam_Q", get_lam_Q_offset(),
				PT_DESCRIPTION, "Lagrange multiplier on reactive power mismatch (u/MVAr)",
				PT_ACCESS, PA_REFERENCE,

			PT_double, "mu_Vmax", get_mu_Vmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper voltage limit (u/p.u.)",
				PT_ACCESS, PA_REFERENCE,

			PT_double, "mu_Vmin", get_mu_Vmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower voltage limit (u/p.u.)",
				PT_ACCESS, PA_REFERENCE,

			NULL)<1){
				char msg[256];
				snprintf(msg,sizeof(msg)-1, "unable to publish properties in %s",__FILE__);
				throw msg;
		}
	}
}

int bus::create(void) 
{
	extern bus *buslist[MAXENT];
	extern size_t nbus;
	if ( nbus < MAXENT )
	{
		buslist[nbus++] = this;
	}
	else
	{
		throw "maximum bus entities exceeded";
	}

	return 1; // return 1 on success, 0 on failure
}

int bus::init(OBJECT *parent)
{
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}
