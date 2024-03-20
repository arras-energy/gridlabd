// module/pypower/powerline.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(powerline);
EXPORT_INIT(powerline);
EXPORT_SYNC(powerline);

CLASS *powerline::oclass = NULL;
powerline *powerline::defaults = NULL;

powerline::powerline(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"powerline",sizeof(powerline),PC_PRETOPDOWN|PC_BOTTOMUP|PC_AUTOLOCK|PC_OBSERVER);
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

			PT_double, "susceptance[S/mile]", get_susceptance_offset(),
				PT_DESCRIPTION, "line susceptance (S/mile)",

			PT_enumeration, "status", get_status_offset(),
				PT_DEFAULT, "IN",
				PT_KEYWORD, "IN", (enumeration)PLS_IN,
				PT_KEYWORD, "OUT", (enumeration)PLS_OUT,
				PT_DESCRIPTION, "line status (IN or OUT)",

			PT_enumeration, "composition", get_composition_offset(),
				PT_KEYWORD, "NONE", (enumeration)PLC_NONE,
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
	Z = complex(0,0);
	Y = complex(0,0);
	b = 0.0;
	ratio = 1.0;
	angle = 0.0;
	rating = 0.0;
	
	return 1; // return 1 on success, 0 on failure
}

int powerline::init(OBJECT *parent_hdr)
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
			if ( parent->get_impedance().Re() != 0 || parent->get_impedance().Im() != 0 )
			{
				error("parent '%s' non-zero impedance would be overwritten",get_parent()->get_name());
				return 0;
			}
			else if ( parent->get_composition() == PLC_NONE )
			{
				error("parent '%s' does not specify powerline composition",get_parent()->get_name());
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
		warning("powerline without parent does nothing");
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

	b = get_susceptance()*length;

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP powerline::presync(TIMESTAMP t0)
{
	if ( get_parent() != NULL && get_impedance().Re() == 0 && get_impedance().Im() == 0 )
	{
		Y = Z = complex(0,0);
		b = 0.0;
	}
	return TS_NEVER;
}

TIMESTAMP powerline::sync(TIMESTAMP t0)
{
	if ( get_parent() != NULL )
	{
		if ( parent_is_branch )
		{
			branch *parent = (branch*)get_parent();

			if ( get_status() == PLS_IN )
			{
				// copy status/impedance/admittance values to branch
				parent->set_r(get_Z().Re());
				parent->set_x(get_Z().Im());
				parent->set_b(get_b());
				parent->set_rateA(get_rateA());
				parent->set_status(branch::BS_IN);
			}
			else
			{
				parent->set_status(branch::BS_OUT);
			}
		}
		else if ( get_status() == PLS_IN )
		{
			powerline *parent = (powerline*)get_parent();
			if ( parent->get_composition() == PLC_SERIES )
			{
				// add impedance
				complex Z = parent->get_Z() + get_Z();
				parent->set_Z(Z);
				parent->set_Y(Z.Inv());
				parent->set_b(parent->get_b() + get_b());
				parent->set_rateA(min(parent->get_rateA(),get_rateA()));
			}
			else if ( parent->get_composition() == PLC_PARALLEL )
			{
				complex Y = parent->get_Y() + get_Y();
				parent->set_Y(Y);
				parent->set_Z(Y.Inv());
				parent->set_b(parent->get_b() + get_b());
				parent->set_rateA(parent->get_rateA()+get_rateA());
			}
			else
			{
				exception("invalid powerline composition value '%d' encountered",get_composition());
			}
		}
	}
	return TS_NEVER;
}

