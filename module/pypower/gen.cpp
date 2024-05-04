// module/pypower/gen.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(gen);
EXPORT_INIT(gen);

CLASS *gen::oclass = NULL;
gen *gen::defaults = NULL;

gen::gen(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"gen",sizeof(gen),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class gen";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_int32, "bus", get_bus_offset(),
				PT_DESCRIPTION, "bus number",

			PT_double, "Pg[MW]", get_Pg_offset(),
				PT_DESCRIPTION, "real power output (MW)",

			PT_double, "Qg[MVAr]", get_Qg_offset(),
				PT_DESCRIPTION, "reactive power output (MVAr)",

			PT_double, "Qmax[MVAr]", get_Qmax_offset(),
				PT_DESCRIPTION, "maximum reactive power output (MVAr)",

			PT_double, "Qmin[MVAr]", get_Qmin_offset(),
				PT_DESCRIPTION, "minimum reactive power output (MVAr)",

			PT_double, "Vg[pu*V]", get_Vg_offset(),
				PT_DESCRIPTION, "voltage magnitude setpoint (p.u.)",

			PT_double, "mBase[MVA]", get_mBase_offset(),
				PT_DESCRIPTION, "total MVA base of machine, defaults to baseMVA",

			PT_enumeration, "status", get_status_offset(),
				PT_DESCRIPTION, "1 - in service, 0 - out of service",
				PT_KEYWORD, "IN_SERVICE", (enumeration)1,
				PT_KEYWORD, "OUT_OF_SERVICE", (enumeration)0,

			PT_double, "Pmax[MW]", get_Pmax_offset(),
				PT_DESCRIPTION, "maximum real power output (MW)",

			PT_double, "Pmin[MW]", get_Pmin_offset(),
				PT_DESCRIPTION, "minimum real power output (MW)",

			PT_double, "Pc1[MW]", get_Pc1_offset(),
				PT_DESCRIPTION, "lower real power output of PQ capability curve (MW)",

			PT_double, "Pc2[MW]", get_Pc2_offset(),
				PT_DESCRIPTION, "upper real power output of PQ capability curve (MW)",

			PT_double, "Qc1min[MVAr]", get_Qc1min_offset(),
				PT_DESCRIPTION, "minimum reactive power output at Pc1 (MVAr)",

			PT_double, "Qc1max[MVAr]", get_Qc1max_offset(),
				PT_DESCRIPTION, "maximum reactive power output at Pc1 (MVAr)",

			PT_double, "Qc2min[MVAr]", get_Qc2min_offset(),
				PT_DESCRIPTION, "minimum reactive power output at Pc2 (MVAr)",

			PT_double, "Qc2max[MVAr]", get_Qc2max_offset(),
				PT_DESCRIPTION, "maximum reactive power output at Pc2 (MVAr)",

			PT_double, "ramp_agc[MW/min]", get_ramp_agc_offset(),
				PT_DESCRIPTION, "ramp rate for load following/AGC (MW/min)",

			PT_double, "ramp_10[MW]", get_ramp_10_offset(),
				PT_DESCRIPTION, "ramp rate for 10 minute reserves (MW)",

			PT_double, "ramp_30[MW]", get_ramp_30_offset(),
				PT_DESCRIPTION, "ramp rate for 30 minute reserves (MW)",

			PT_double, "ramp_q[MVAr/min]", get_ramp_q_offset(),
				PT_DESCRIPTION, "ramp rate for reactive power (2 sec timescale) (MVAr/min)",

			PT_double, "apf", get_apf_offset(),
				PT_DESCRIPTION, "area participation factor",

			PT_double, "mu_Pmax[pu/MW]", get_mu_Pmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper Pg limit (p.u./MW)",

			PT_double, "mu_Pmin[pu/MW]", get_mu_Pmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower Pg limit (p.u./MW)",

			PT_double, "mu_Qmax[pu/MVAr]", get_mu_Qmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper Qg limit (p.u./MVAr)",

			PT_double, "mu_Qmin[pu/MVAr]", get_mu_Qmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower Qg limit (p.u./MVAr)",

			NULL)<1)
		{
				throw "unable to publish gen properties";
		}
	}
}

int gen::create(void) 
{
	extern gen *genlist[MAXENT];
	extern size_t ngen;
	if ( ngen < MAXENT )
	{
		genlist[ngen++] = this;
	}
	else
	{
		throw "maximum gen entities exceeded";
	}

	extern double base_MVA;
	mBase = base_MVA;
	cost = NULL;

	return 1; /* return 1 on success, 0 on failure */
}

int gen::init(OBJECT *parent)
{
	return 1;
}
