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

			PT_char32, "city", get_city_offset(),
			
			PT_char32, "state", get_state_offset(),
			
			PT_char32, "zipcode", get_zipcode_offset(),
			
			PT_char32, "country", get_country_offset(),
			
			PT_char32, "naics_code", get_naics_code_offset(),
			
			PT_char256, "naics_description", get_naics_description_offset(),
			
			PT_enumeration, "plant_type", get_plant_type_offset(),

			PT_enumeration, "status", get_status_offset(),

			PT_int32, "plant_code", get_plant_code(),
			
			PT_double, "operating_capacity[MW]", get_operating_capacity_offset(),
			
			PT_double, "summer_capacity[MW]", get_summer_capacity_offset(),
			
			PT_double, "winter_capacity[MW]", get_winter_capacity_offset(),
			
			PT_double, "capacity_factor[pu]", get_capacity_factor_offset(),
			
			PT_enumeration, "primary_fuel", get_primary_fuel_offset(),

			PT_enumeration, "secondary_fuel", get_secondary_fuel_offset(),

			PT_object, "substation_1", get_substation_1_offset(),

			PT_object, "substation_2", get_substation_2_offset(),

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
	gen *parent = (gen*)get_parent();
	if ( ! parent->isa("gen","pypower") )
	{
		error("parent '%s' is not a pypower gen object",get_parent()->get_name());
		return 0;
	}

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP powerplant::presync(TIMESTAMP t1)
{
	// copy data to parent
	// bus *parent = (bus*)get_parent();
	// complex Vpu = V / Vn;
	// S = P + ~(I + Z*Vpu)*Vpu;
	// parent->set_Pd(S.Re());
	// parent->set_Qd(S.Im());
	return TS_NEVER;
}

TIMESTAMP powerplant::sync(TIMESTAMP t1)
{
	return TS_NEVER;
}

TIMESTAMP powerplant::postsync(TIMESTAMP t1)
{
	// copy data from parent
	// bus *parent = (bus*)get_parent();
	// V.SetPolar(parent->get_Vm()*Vn,parent->get_Va());
	return TS_NEVER;
}
