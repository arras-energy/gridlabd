// module/pypower/transformer.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(transformer);
EXPORT_INIT(transformer);
EXPORT_PRECOMMIT(transformer);

CLASS *transformer::oclass = NULL;
transformer *transformer::defaults = NULL;

transformer::transformer(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"transformer",sizeof(transformer),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class transformer";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_complex, "impedance[Ohm]", get_impedance_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "transformer impedance (Ohm)",

			PT_enumeration, "status", get_status_offset(),
				PT_DEFAULT, "IN",
				PT_KEYWORD, "IN", (enumeration)TS_IN,
				PT_KEYWORD, "OUT", (enumeration)TS_OUT,
				PT_DESCRIPTION, "transformer status (IN or OUT)",

			PT_double, "turns_ratio[pu]", get_turns_ratio_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "coil turns ratio (pu)",

			PT_double, "phase_shift[deg]", get_phase_shift_offset(),
				PT_DESCRIPTION, "transformer phase shift (deg) - use 30 for DY or YD transformers",

			NULL) < 1 )
		{
				throw "unable to publish transformer properties";
		}
	}
}

int transformer::create(void) 
{
	parent_is_branch = false;
	return 1; // return 1 on success, 0 on failure
}

int transformer::init(OBJECT *parent_hdr)
{
	powerline *parent = (powerline*)get_parent();
	if ( parent ) 
	{
		if ( parent->isa("branch","pypower") )
		{
			branch *parent = (branch*)get_parent();
			parent_is_branch = true;
			int32 n_children = parent->get_child_count();
			if ( n_children > 0 )
			{
				error("branch '%s' cannot accept more than one child component",get_parent()->get_name());
				return 0;
			}
			parent->set_child_count(n_children+1);
		}
		else
		{
			error("parent '%s' is not a pypower branch",get_parent()->get_name());
			return 0;
		}

	}
	else
	{
		warning("transformer without parent does nothing");
	}

	// check impedance
	if ( impedance.Re() == 0 && impedance.Im() == 0 )
	{
		error("transformer impedance must be positive");
		return 0;
	}

	// check ratio
	if ( get_turns_ratio() <= 0 )
	{
		error("turns ratio must be strictly positive");
		return 0;
	}

	// check angle
	if ( fabs(get_phase_shift()) > 360 )
	{
		warning("phase shift value %.4lg seems unlikely to be valid",get_phase_shift());
	}

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP transformer::precommit(TIMESTAMP t0)
{
	if ( get_parent() != NULL )
	{
		if ( parent_is_branch )
		{
			branch *parent = (branch*)get_parent();

			if ( get_status() == TS_IN )
			{
				// copy status/impedance/admittance values to branch
				parent->set_r(get_impedance().Re());
				parent->set_x(get_impedance().Im());
				parent->set_b(get_impedance().Inv().Im());
				parent->set_ratio(get_turns_ratio());
				parent->set_angle(get_phase_shift());
				parent->set_rateA(get_rating());
				parent->set_status(branch::BS_IN);
			}
			else
			{
				parent->set_status(branch::BS_OUT);
			}
		}
	}
	return TS_NEVER;
}

