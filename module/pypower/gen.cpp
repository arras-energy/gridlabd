// module/pypower/gen.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(gen);
EXPORT_INIT(gen);
EXPORT_PRECOMMIT(gen);

CLASS *gen::oclass = NULL;
gen *gen::defaults = NULL;

double gen::default_reactive_power_fraction = 0.2;

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

			PT_double, "Vg[pu.kV]", get_Vg_offset(),
				PT_DEFAULT, "1 pu.kV",
				PT_DESCRIPTION, "voltage magnitude setpoint (per unit)",

			PT_double, "mBase[MVA]", get_mBase_offset(),
				PT_DEFAULT, "100 MVA",
				PT_DESCRIPTION, "total MVA base of machine, defaults to baseMVA",

			PT_enumeration, "status", get_status_offset(),
				PT_KEYWORD, "IN_SERVICE", (enumeration)1,
				PT_KEYWORD, "OUT_OF_SERVICE", (enumeration)0,
				PT_DEFAULT, "IN_SERVICE",
				PT_DESCRIPTION, "1 - in service, 0 - out of service",

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

			PT_double, "mu_Pmax[pu./MW]", get_mu_Pmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper Pg limit (per unit/MW)",

			PT_double, "mu_Pmin[pu./MW]", get_mu_Pmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower Pg limit (per unit/MW)",

			PT_double, "mu_Qmax[pu./MVAr]", get_mu_Qmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper Qg limit (per unit/MVAr)",

			PT_double, "mu_Qmin[pu./MVAr]", get_mu_Qmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower Qg limit (per unit/MVAr)",

			NULL)<1)
		{
				throw "unable to publish gen properties";
		}

	    gl_global_create("pypower::default_reactive_power_fraction[pu]",
	        PT_double, &default_reactive_power_fraction, 
	        PT_DESCRIPTION, "Default fraction of real power generation available for reactive power",
	        NULL);

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
	cost = NULL;
	plant_count = 0;
	bus = 0; // flag for unset

	return 1; /* return 1 on success, 0 on failure */
}

int gen::init(OBJECT *parent)
{
	class bus *p = OBJECTDATA(parent,class bus);
	if ( parent == NULL )
	{
		error("cannot find bus id without a known parent");
		return 0;
	}
	if ( ! p->isa("bus","pypower") )
	{
		error("parent object '%s' is not a pypower bus",p->get_name());
		return 0;
	}
	if ( get_bus() == 0 )
	{
		if ( p->get_bus_i() == 0 )
		{
			return 2; // defer until bus is initialized
		}
		set_bus(p->get_bus_i());
		verbose("setting bus index to %d",bus);
	}
	else if ( get_bus() != p->get_bus_i() )
	{
		error("parent object '%s' bus index mismatch",p->get_name());
		return 0;		
	}

	return 1;
}

TIMESTAMP gen::precommit(TIMESTAMP t0)
{
	// reset capacity accumulators if powerplant are providing this data
	if ( plant_count > 0 )
	{
		Pmax = 0.0;
		Pg = 0.0;
		Qg = 0.0;
	}
	return TS_NEVER;
}

unsigned int gen::get_powerplant_count(void)
{
	return plant_count;
}

void gen::add_powerplant(class powerplant *plant)
{
	gl_debug("powerplant '%s' connected",plant->get_name());
	plant_count++;
}

void gen::add_Pg(double real)
{
	Pg += real;
}

void gen::add_Qg(double reactive)
{
	Qg += reactive;
}

void gen::add_Pmax(double capacity)
{
	Pmax += capacity;
	Qmax = Pmax/default_reactive_power_fraction; 
	Qmin = -Qmax;
}

void gen::add_cost(class gencost *add)
{
	if ( cost == NULL )
	{
		cost = add;
	}

	// only identical cost models can be "added" together
	else if ( ! cost->is_equal(add) )
	{
		error("unable to add to different gencost models");
	}
}
