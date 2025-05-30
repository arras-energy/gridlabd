// module/pypower/branch.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(branch);
EXPORT_INIT(branch);

CLASS *branch::oclass = NULL;
branch *branch::defaults = NULL;

branch::branch(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"branch",sizeof(branch),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class branch";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,
			PT_object, "from", get_from_offset(),
				PT_DESCRIPTION, "from bus name",

			PT_object, "to", get_to_offset(),
				PT_DESCRIPTION, "to bus name",
				
			PT_int32, "fbus", get_fbus_offset(),
				PT_DESCRIPTION, "from bus number",

			PT_int32, "tbus", get_tbus_offset(),
				PT_DESCRIPTION, "to bus number",

			PT_double, "r[pu.Ohm]", get_r_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "resistance (per unit)",

			PT_double, "x[pu.Ohm]", get_x_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "reactance (per unit)",

			PT_double, "b[pu.S]", get_b_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "total line charging susceptance (per unit)",

			PT_double, "rateA[MVA]", get_rateA_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "MVA rating A (long term rating)",

			PT_double, "rateB[MVA]", get_rateB_offset(),
				PT_DESCRIPTION, "MVA rating B (short term rating)",
				
			PT_double, "rateC[MVA]", get_rateC_offset(),
				PT_DESCRIPTION, "MVA rating C (emergency term rating)",
			
			PT_double, "ratio[pu]", get_ratio_offset(),
				PT_DEFAULT, "1 pu",
				PT_DESCRIPTION, "transformer off nominal turns ratio",

			PT_double, "angle[deg]", get_angle_offset(),
				PT_DEFAULT, "0 deg",
				PT_DESCRIPTION, "transformer phase shift angle (degrees)",

			PT_enumeration, "status", get_status_offset(),
				PT_KEYWORD,"OUT",(enumeration)BS_OUT,
				PT_KEYWORD,"IN",(enumeration)BS_IN,
				PT_DEFAULT, "IN",
				PT_DESCRIPTION, "initial branch status, IN=1 - in service, OUT=0 - out of service",

			PT_double, "angmin[deg]", get_angmin_offset(),
				PT_DEFAULT, "-360 deg",
				PT_DESCRIPTION, "minimum angle difference, angle(Vf) - angle(Vt) (degrees)",

			PT_double, "angmax[deg]", get_angmax_offset(),
				PT_DEFAULT, "360 deg",
				PT_DESCRIPTION, "maximum angle difference, angle(Vf) - angle(Vt) (degrees)",

			PT_complex, "current[A]", get_current_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "line current (A)",

			PT_double, "loss[MW]", get_loss_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "line loss (MW)",

			NULL)<1)
		{
				throw "unable to publish branch properties";
		}
	}
}

int branch::create(void) 
{
	extern branch *branchlist[MAXENT];
	extern size_t nbranch;
	if ( nbranch < MAXENT )
	{
		branchlist[nbranch++] = this;
	}
	else
	{
		throw "maximum branch entities exceeded";
	}
	fbus = tbus = 0; // flag for unset

	set_from("");
	set_to("");
	set_fbus(0);
	set_tbus(0);
	set_r(0.0);
	set_x(0.0);
	set_b(0.0);
	set_rateA(0.0);
	set_rateB(0.0);
	set_rateC(0.0);
	set_ratio(0.0);
	set_angle(0.0);
	set_status(BS_OUT);
	set_angmin(-360.0);
	set_angmax(360.0);
	set_child_count(0);
	set_current(0.0);
	set_loss(0.0);

	return 1; /* return 1 on success, 0 on failure */
}

int branch::init(OBJECT *parent)
{
	if ( get_from() == NULL || get_to() == NULL )
	{
		error("from or to bus not specified");
		return 0;
	}
	// automatic bus lookup
	if ( get_fbus() == 0 )
	{
		bus *f = OBJECTDATA(get_from(),bus);
		if ( f == NULL )
		{
			error("cannot determine 'fbus' if 'from' is not specified");
			return 0;
		}
		if ( f->isa("bus","pypower") )
		{
			if ( f->get_bus_i() == 0 )
			{
				return 2; // defer until bus is initialized
			}
			set_fbus(f->get_bus_i());
		}
		else
		{
			error("from object '%s' is not a pypower bus",f->get_name());
			return 0;
		}
	}
	if ( get_tbus() == 0 )
	{
		bus *t = OBJECTDATA(get_to(),bus);
		if ( t == NULL )
		{
			error("cannot determine 'tbus' if 'to' is not specified");
			return 0;
		}
		if ( t->isa("bus","pypower") )
		{
			if ( t->get_bus_i() == 0 )
			{
				return 2; // defer until bus is initialized
			}
			set_tbus(t->get_bus_i());
		}
		else
		{
			error("from object '%s' is not a pypower bus",t->get_name());
			return 0;
		}
	}
	if ( ratio == 0 )
	{
		ratio = 1.0;
	}
	if ( x == 0 )
	{
		warning("x is zero");
	}
	if ( rateA == 0 )
	{
		warning("rateA is zero");
	}
	if ( rateB > 0 && rateB < rateA )
	{
		warning("rateB is less than rateA");
	}
	if ( rateC > 0 && rateC < rateB )
	{
		warning("rateC is less than rateB");
	}
	if ( angmin == 0 )
	{
		angmin = -360;
	}
	if ( angmax == 0 )
	{
		angmax = +360;
	}
	return 1;
}
