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

			PT_complex, "impedance[Ohm/mile]", get_impedance_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "line impedance (Ohm/mile)",

			PT_enumeration, "status", get_status_offset(),
				PT_DEFAULT, "IN",
				PT_KEYWORD, "IN", (enumeration)TS_IN,
				PT_KEYWORD, "OUT", (enumeration)TS_OUT,
				PT_DESCRIPTION, "transformer status (IN or OUT)",

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
				error("parent '%s' cannot accept more than one child component",get_parent()->get_name());
				return 0;
			}
			parent->set_child_count(n_children+1);
		}
		else if ( parent->isa("powerline","pypower") )
		{
			if ( ( parent->get_impedance().Re() != 0 || parent->get_impedance().Im() != 0 ) 
				&& ( parent->get_length() > 0 ) )
			{
				error("parent '%s' non-zero impedance will be overwritten",get_parent()->get_name());
				return 0;
			}
			if ( parent->get_composition() == powerline::PLC_PARALLEL )
			{
				error("parent '%s' must have series composition",get_parent()->get_name());
				return 0;
			}
		}
		else
		{
			error("parent '%s' is not a pypower branch or powerline",get_parent()->get_name());
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
				parent->set_status(1);
			}
			else
			{
				parent->set_status(0);
			}
		}
		else 
		{
			powerline *parent = (powerline*)get_parent();
			if ( get_status() == TS_IN )
			{
				// add impedance
				complex Z = parent->get_Z() + get_impedance();
				parent->set_Z(Z);
				parent->set_Y(Z.Inv());
				parent->set_ratio(parent->get_ratio()*get_turns_ratio());
				parent->set_angle(parent->get_angle()+get_phase_shift());
				parent->set_rateA(min(parent->get_rateA(),get_rating()));
			}
			else
			{
				parent->set_status(powerline::PLS_IN);
			}
		}
	}
	return TS_NEVER;
}

