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
			PT_int32, "fbus", get_fbus_offset(),
				PT_DESCRIPTION, "from bus number",

			PT_int32, "tbus", get_tbus_offset(),
				PT_DESCRIPTION, "to bus number",

			PT_double, "r[pu*Ohm]", get_r_offset(),
				PT_DESCRIPTION, "resistance (p.u.)",

			PT_double, "x[pu*Ohm]", get_x_offset(),
				PT_DESCRIPTION, "reactance (p.u.)",

			PT_double, "b[pu/Ohm]", get_b_offset(),
				PT_DESCRIPTION, "total line charging susceptance (p.u.)",

			PT_double, "rateA[MVA]", get_rateA_offset(),
				PT_DESCRIPTION, "MVA rating A (long term rating)",

			PT_double, "rateB[MVA]", get_rateB_offset(),
				PT_DESCRIPTION, "MVA rating B (short term rating)",
				
			PT_double, "rateC[MVA]", get_rateC_offset(),
				PT_DESCRIPTION, "MVA rating C (emergency term rating)",
			
			PT_double, "ratio[pu]", get_ratio_offset(),
				PT_DESCRIPTION, "transformer off nominal turns ratio",

			PT_double, "angle[pu]", get_angle_offset(),
				PT_DESCRIPTION, "transformer phase shift angle (degrees)",

			PT_int32, "status", get_status_offset(),
				PT_DESCRIPTION, "initial branch status, 1 - in service, 0 - out of service",

			PT_double, "angmin[deg]", get_angmin_offset(),
				PT_DESCRIPTION, "minimum angle difference, angle(Vf) - angle(Vt) (degrees)",

			PT_double, "angmax[deg]", get_angmax_offset(),
				PT_DESCRIPTION, "maximum angle difference, angle(Vf) - angle(Vt) (degrees)",

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

	return 1; /* return 1 on success, 0 on failure */
}

int branch::init(OBJECT *parent)
{
	return 1;
}
