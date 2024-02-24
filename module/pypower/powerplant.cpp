// module/pypower/powerplant.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(powerplant);
EXPORT_INIT(powerplant);
EXPORT_SYNC(powerplant);

CLASS *powerplant::oclass = NULL;
powerplant *powerplant::defaults = NULL;

powerplant::powerplant(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"powerplant",sizeof(powerplant),PC_PRETOPDOWN|PC_POSTTOPDOWN|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class powerplant";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_complex, "S[VA]", get_S_offset(),
				PT_DESCRIPTION, "total power demand (VA)",

			PT_complex, "Z[VA]", get_Z_offset(),
				PT_DESCRIPTION, "constant impedance powerplant (W)",

			PT_complex, "I[VA]", get_I_offset(),
				PT_DESCRIPTION, "constant current powerplant (W)",

			PT_complex, "P[VA]", get_P_offset(),
				PT_DESCRIPTION, "constant power powerplant (W)",

			PT_complex, "V[V]", get_V_offset(),
				PT_DESCRIPTION, "bus voltage (V)",

			PT_double, "Vn[V]", get_Vn_offset(),
				PT_DESCRIPTION, "nominal voltage (V)",

			NULL) < 1 )
		{
				throw "unable to publish powerplant properties";
		}
	}
}

int powerplant::create(void) 
{
	return 1; // return 1 on success, 0 on failure
}

int powerplant::init(OBJECT *parent_hdr)
{
	bus *parent = (bus*)get_parent();
	if ( ! parent->isa("gen","pypower") )
	{
		error("parent '%s' is not a pypower gen object",get_parent()->get_name());
		return 0;
	}

	if ( Vn == 0.0 )
	{
		error("nominal voltage (Vn) not set");
		return 0;
	}
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP powerplant::presync(TIMESTAMP t1)
{
	// copy data to parent
	bus *parent = (bus*)get_parent();
	complex Vpu = V / Vn;
	S = P + ~(I + Z*Vpu)*Vpu;
	parent->set_Pd(S.Re());
	parent->set_Qd(S.Im());
	return TS_NEVER;
}

TIMESTAMP powerplant::sync(TIMESTAMP t1)
{
	return TS_NEVER;
}

TIMESTAMP powerplant::postsync(TIMESTAMP t1)
{
	// copy data from parent
	bus *parent = (bus*)get_parent();
	V.SetPolar(parent->get_Vm()*Vn,parent->get_Va());
	return TS_NEVER;
}
