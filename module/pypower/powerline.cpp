// module/pypower/powerline.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(powerline);
EXPORT_INIT(powerline);
EXPORT_PRECOMMIT(powerline);

CLASS *powerline::oclass = NULL;
powerline *powerline::defaults = NULL;

powerline::powerline(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"powerline",sizeof(powerline),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class powerline";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_double, "length[mile]", get_length_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "length (miles)",

			PT_complex, "impedance[Ohm/mile]", get_impedance_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "line impedance (Ohm/mile)",

			PT_enumeration, "status", get_status_offset(),
				PT_DEFAULT, "IN",
				PT_KEYWORD, "IN", (enumeration)PLS_IN,
				PT_KEYWORD, "OUT", (enumeration)PLS_OUT,
				PT_DESCRIPTION, "line status (IN or OUT)",

			PT_enumeration, "composition", get_composition_offset(),
				PT_KEYWORD, "SERIES", (enumeration)PLC_SERIES,
				PT_KEYWORD, "PARALLEL", (enumeration)PLC_PARALLEL,
				PT_DESCRIPTION, "parent line composition (SERIES or PARALLEL)",

			NULL) < 1 )
		{
				throw "unable to publish powerline properties";
		}
	}
}

int powerline::create(void) 
{
	parent_is_branch = false;
	return 1; // return 1 on success, 0 on failure
}

int powerline::init(OBJECT *parent_hdr)
{
	powerline *parent = (powerline*)get_parent();
	if ( parent ) 
	{
		if ( parent->isa("branch","pypower") )
		{
			parent_is_branch = true;
		}
		else if ( parent->isa("powerline","pypower") )
		{
			if ( ( parent->get_impedance().Re() != 0 || parent->get_impedance().Im() != 0 ) 
				&& ( parent->get_length() > 0 ) )
			{
				error("parent '%s' non-zero impedance will be overwritten",get_parent()->get_name());
				return 0;
			}
		}
		else
		{
			error("parent '%s' is not a pypower branch or powerline",get_parent()->get_name());
			return 0;
		}

	}

	// check impedance
	if ( impedance.Re() != 0 || impedance.Im() != 0 )
	{
		if ( length <= 0 )
		{
			error("line length must be positive to calculate impedance and admittance");
			return 0;
		}
		Z = impedance * length;
		Y = Z.Inv();
	}

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP powerline::precommit(TIMESTAMP t0)
{
	if ( get_parent() != NULL )
	{
		if ( parent_is_branch )
		{
			branch *parent = (branch*)get_parent();
			// copy impedance/admittance values to branch
			parent->set_r(get_Z().Re());
			parent->set_x(get_Z().Im());
			parent->set_b(get_Y().Im());
		}
		else
		{
			powerline *parent = (powerline*)get_parent();
			if ( parent->get_composition() == PLC_SERIES )
			{
				// add impedance
				complex Z = parent->get_Z() + get_Z();
				parent->set_Z(Z);
				parent->set_Y(Z.Inv());

			}
			else if ( parent->get_composition() == PLC_PARALLEL )
			{
				complex Y = parent->get_Y() + get_Y();
				parent->set_Y(Y);
				parent->set_Z(Y.Inv());
			}
			else
			{
				exception("invalid powerline composition value '%d' encountered",get_composition());
			}
		}
	}
	return TS_NEVER;
}

