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
			
			PT_set, "generator", get_generator_offset(), 
			    PT_KEYWORD, "UNKNOWN", (set)0x00000001, 
			    PT_KEYWORD, "HT", (set)0x00000002, // hydro turbine
			    PT_KEYWORD, "ST", (set)0x00000004, // steam turbine
			    PT_KEYWORD, "AT", (set)0x00000008, // compressed air turbine
			    PT_KEYWORD, "IC", (set)0x00000010, // internal combustion
			    PT_KEYWORD, "FW", (set)0x00000020, // flywheel
			    PT_KEYWORD, "WT", (set)0x00000040, // wind turbine
			    PT_KEYWORD, "ES", (set)0x00000080, // energy storage inverter
			    PT_KEYWORD, "CT", (set)0x00000100, // combustion turbine
			    PT_KEYWORD, "PV", (set)0x00000200, // photovoltaic inverter
			    PT_KEYWORD, "CC", (set)0x00000400, // combined cycle turbine

			PT_enumeration, "status", get_status_offset(),
				PT_KEYWORD, "OFFLINE", (enumeration)0x00,
				PT_KEYWORD, "ONLINE", (enumeration)0x01,
				// PT_KEYWORD, "OP", (enumeration)0x01,

			PT_int32, "plant_code", get_plant_code(),
			
			PT_double, "operating_capacity[MW]", get_operating_capacity_offset(),
			
			PT_double, "summer_capacity[MW]", get_summer_capacity_offset(),
			
			PT_double, "winter_capacity[MW]", get_winter_capacity_offset(),
			
			PT_double, "capacity_factor[pu]", get_capacity_factor_offset(),
			
			PT_set, "fuel", get_fuel_offset(), 
			    PT_KEYWORD, "ELEC", (set)0x00000001, 
			    PT_KEYWORD, "WIND", (set)0x00000002,
			    PT_KEYWORD, "SUN", (set)0x00000004, 
			    PT_KEYWORD, "GEO", (set)0x00000008, 
			    PT_KEYWORD, "COKE", (set)0x00000010, 
			    PT_KEYWORD, "WASTE", (set)0x00000020, 
			    PT_KEYWORD, "BIO", (set)0x00000040, 
			    PT_KEYWORD, "OIL", (set)0x00000080, 
			    PT_KEYWORD, "UNKNOWN", (set)0x00000100, 
			    PT_KEYWORD, "WOOD", (set)0x00000200, 
			    PT_KEYWORD, "OTHER", (set)0x00000400, 
			    PT_KEYWORD, "GAS", (set)0x00000800, 
			    PT_KEYWORD, "NUC", (set)0x00001000, 
			    PT_KEYWORD, "WATER", (set)0x00002000, 
			    PT_KEYWORD, "COAL", (set)0x00004000, 
			    PT_KEYWORD, "NG", (set)0x00008000, 

			PT_char256, "substation_1", get_substation_1_offset(),

			PT_char256, "substation_2", get_substation_2_offset(),

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
	if ( parent && ! parent->isa("gen","pypower") )
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
