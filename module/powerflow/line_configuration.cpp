/** $Id: line_configuration.cpp 4738 2014-07-03 00:55:39Z dchassin $
	Copyright (C) 2008 Battelle Memorial Institute
	@file line_configuration.cpp
	@addtogroup line_configuration 
	@ingroup line

	@{
**/

#include "powerflow.h"


//////////////////////////////////////////////////////////////////////////
// line_configuration CLASS FUNCTIONS
//////////////////////////////////////////////////////////////////////////

CLASS* line_configuration::oclass = NULL;
CLASS* line_configuration::pclass = NULL;

line_configuration::line_configuration(MODULE *mod) : powerflow_library(mod)
{
	if(oclass == NULL)
	{
		oclass = gl_register_class(mod,"line_configuration",sizeof(line_configuration),PC_NOSYNC);
		if (oclass==NULL)
			throw "unable to register class line_configuration";
		else
			oclass->trl = TRL_PROVEN;
        
        if(gl_publish_variable(oclass,
			PT_object, "conductor_A",PADDR(phaseA_conductor),
			PT_object, "conductor_B",PADDR(phaseB_conductor),
			PT_object, "conductor_C",PADDR(phaseC_conductor),
			PT_object, "conductor_N",PADDR(phaseN_conductor),
			PT_object, "spacing",PADDR(line_spacing),
			PT_complex, "z11[Ohm/mile]",PADDR(impedance11),
				PT_DEFAULT, "0+0j",
			PT_complex, "z12[Ohm/mile]",PADDR(impedance12),
				PT_DEFAULT, "0+0j",
			PT_complex, "z13[Ohm/mile]",PADDR(impedance13),
				PT_DEFAULT, "0+0j",
			PT_complex, "z21[Ohm/mile]",PADDR(impedance21),
				PT_DEFAULT, "0+0j",
			PT_complex, "z22[Ohm/mile]",PADDR(impedance22),
				PT_DEFAULT, "0+0j",
			PT_complex, "z23[Ohm/mile]",PADDR(impedance23),
				PT_DEFAULT, "0+0j",
			PT_complex, "z31[Ohm/mile]",PADDR(impedance31),
				PT_DEFAULT, "0+0j",
			PT_complex, "z32[Ohm/mile]",PADDR(impedance32),
				PT_DEFAULT, "0+0j",
			PT_complex, "z33[Ohm/mile]",PADDR(impedance33),
				PT_DEFAULT, "0+0j",
			PT_double, "c11[nF/mile]",PADDR(capacitance11),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c12[nF/mile]",PADDR(capacitance12),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c13[nF/mile]",PADDR(capacitance13),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c21[nF/mile]",PADDR(capacitance21),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c22[nF/mile]",PADDR(capacitance22),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c23[nF/mile]",PADDR(capacitance23),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c31[nF/mile]",PADDR(capacitance31),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c32[nF/mile]",PADDR(capacitance32),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "c33[nF/mile]",PADDR(capacitance33),
				PT_DEFAULT, "0 nF/mile",
			PT_double, "rating.summer.continuous[A]", PADDR(summer.continuous),
				PT_DEFAULT, "1000 A",
				PT_DESCRIPTION,"amp rating in summer, continuous",
			PT_double, "rating.summer.emergency[A]", PADDR(summer.emergency),
				PT_DEFAULT, "2000 A",
				PT_DESCRIPTION,"amp rating in summer, short term",
			PT_double, "rating.winter.continuous[A]", PADDR(winter.continuous),
				PT_DEFAULT, "1000 A",
				PT_DESCRIPTION,"amp rating in winter, continuous",
			PT_double, "rating.winter.emergency[A]", PADDR(winter.emergency),
				PT_DEFAULT, "2000 A",
				PT_DESCRIPTION,"amp rating in winter, short term",
            NULL) < 1) GL_THROW("unable to publish line_configuration properties in %s",__FILE__);
    }
}

int line_configuration::create(void)
{
    phaseA_conductor = NULL; 
	phaseB_conductor = NULL;
	phaseC_conductor = NULL;
	phaseN_conductor = NULL;
	line_spacing = NULL;
	return 1;
}

int line_configuration::isa(char *classname)
{
	return strcmp(classname,"line_configuration")==0;
}

//////////////////////////////////////////////////////////////////////////
// IMPLEMENTATION OF CORE LINKAGE: line_configuration
//////////////////////////////////////////////////////////////////////////

/**
* REQUIRED: allocate and initialize an object.
*
* @param obj a pointer to a pointer of the last object in the list
* @param parent a pointer to the parent of this object
* @return 1 for a successfully created object, 0 for error
*/
EXPORT int create_line_configuration(OBJECT **obj, OBJECT *parent)
{
	try
	{
		*obj = gl_create_object(line_configuration::oclass);
		if (*obj!=NULL)
		{
			line_configuration *my = OBJECTDATA(*obj,line_configuration);
			gl_set_parent(*obj,parent);
			return my->create();
		}
		else
			return 0;
	}
	CREATE_CATCHALL(line_configuration);
}
EXPORT TIMESTAMP sync_line_configuration(OBJECT *obj, TIMESTAMP t1, PASSCONFIG pass)
{
	return TS_NEVER;
}

EXPORT int isa_line_configuration(OBJECT *obj, char *classname)
{
	return strcmp(classname,"line_configuration") == 0;
}

/**@}**/
