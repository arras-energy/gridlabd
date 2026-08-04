// module/pypower/branch.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(branch);
EXPORT_INIT(branch);

CLASS *branch::oclass = NULL;
branch *branch::defaults = NULL;

double branch::autosize_angle = 0.0; // 0 = no sizing 

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
				PT_REQUIRED,
				PT_DESCRIPTION, "from bus name",

			PT_object, "to", get_to_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "to bus name",
				
			PT_int32, "fbus", get_fbus_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "from bus number",

			PT_int32, "tbus", get_tbus_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "to bus number",

			PT_double, "r[pu.Ohm]", get_r_offset(),
				PT_DESCRIPTION, "resistance (per unit)",

			PT_double, "x[pu.Ohm]", get_x_offset(),
				PT_DESCRIPTION, "reactance (per unit)",

			PT_double, "b[pu.S]", get_b_offset(),
				PT_DESCRIPTION, "total line charging susceptance (per unit)",

			PT_double, "rateA[MVA]", get_rateA_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "MVA rating A (long term rating)",

			PT_double, "rateB[MVA]", get_rateB_offset(),
				PT_DEFAULT, "0 MVA",
				PT_DESCRIPTION, "MVA rating B (short term rating)",
				
			PT_double, "rateC[MVA]", get_rateC_offset(),
				PT_DEFAULT, "0 MVA",
				PT_DESCRIPTION, "MVA rating C (emergency term rating)",
			
			PT_double, "ratio[pu]", get_ratio_offset(),
				PT_DEFAULT, "0 pu",
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

			PT_double, "mu_sfrom", get_mu_sfrom_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on MVA limit at 'from' bus",

			PT_double, "mu_sto", get_mu_sto_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier on MVA limit at 'to' bus ",

			PT_double, "mu_angmin", get_mu_angmin_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier lower angle difference limit",

			PT_double, "mu_angmax", get_mu_angmax_offset(),
				PT_DESCRIPTION, "Kuhn-Tucker multiplier upper angle difference limit",

			NULL)<1)
		{
				throw "unable to publish branch properties";
		}

	    gl_global_create("pypower::autosize_angle",
	        PT_double, &autosize_angle, 
	        PT_UNITS, "rad",
	        PT_DESCRIPTION, "Autosize voltage angle to use (0 for no autosizing)",
	        NULL);
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
	set_status(BS_IN);
	set_angmin(-360.0);
	set_angmax(360.0);
	set_child_count(0);
	set_current(0.0);
	set_loss(0.0);

	fromKV = 0.0;
	toKV = 0.0;
	length = 0.0;

	return 1; /* return 1 on success, 0 on failure */
}

int branch::init(OBJECT *parent)
{
	// check from bus
	if ( get_from() == NULL )
	{
		error("from bus not specified");
		return 0;
	}
	bus *f = OBJECTDATA(get_from(),bus);
	if ( ! f->isa("bus","pypower") )
	{
		error("from object '%s' is not a pypower bus",f->get_name());
		return 0;
	}
	fobj = get_object(get_from());

	// check to bus
	if ( get_to() == NULL )
	{
		error("to bus not specified");
		return 0;
	}
	bus *t = OBJECTDATA(get_to(),bus);
	if ( ! t->isa("bus","pypower") )
	{
		error("to object '%s' is not a pypower bus",t->get_name());
		return 0;
	}
	tobj = get_object(get_to());

	// automatic bus lookup
	if ( get_fbus() == 0 )
	{
		if ( f->get_bus_i() == 0 )
		{
			return 2; // defer until bus is initialized
		}
		set_fbus(f->get_bus_i());
	}
	if ( get_tbus() == 0 )
	{
		if ( t->get_bus_i() == 0 )
		{
			return 2; // defer until bus is initialized
		}
		set_tbus(t->get_bus_i());
	}

	// autosize angle check
	if ( autosize_angle < 0 )
	{
		error("autosize_angle must be non-negative");
		return 0;
	}
	if ( autosize_angle > PI/2-0.1 )
	{
		warning("autosize_angle should not be 90 deg or greater");
	}

	// rate checks
	if ( rateA < 0 )
	{
		error("rateA must be non-negative");
		return 0;		
	}
	else 
	
	// turns ratio
	if ( ratio < 0 )
	{
		error("turns ratio must be non-negative");
		return 0;
	}

	if ( autosize_angle > 0 )
	{
		if ( rateA == 0 )
		{
			error("rateA %.1lf MW is not specified but is needed for autosizing",rateA);
			return 0;
		}
		if ( rateB > 0 && rateB < rateA )
		{
			warning("rateB is less than rateA, setting rateB equal to rateA");
		}
		rateB = max(rateA,rateB);
		if ( rateC > 0 && rateC < rateB )
		{
			warning("rateC is less than rateB, setting rateC equal to rateB");
		}
		rateC = max(rateB,rateC);

		// branch types:
		//   length == 0 && fromKV!=toKV -> transformer
		//   length == 0 && fromKV == toKV -> switching device
		//   length > 0 -> powerline
		fromKV = f->get_baseKV();
		toKV = t->get_baseKV();
		is_transformer = ( fromKV != toKV );

		// haversine calculation
		length = fobj->get_distance(tobj);
		if ( ! is_transformer && ( r == 0 || x == 0 ) )
		{
			if ( isnan(length) )
			{
				warning("unable to compute default line r/x/b without lat/lon for from/to bus");
			}
			else
			{
				verbose("distance from %.6lf,%.6lf to %.6lf,%.6lf is %.1lf miles\n",
					fobj->get_latitude(),fobj->get_longitude(),
					tobj->get_latitude(),tobj->get_longitude(),
					length);
			}
		}
		else if ( is_transformer && length > 0.01 ) // 60 feet minimum separation
		{
			warning("transformer from and to busses are %.2lf miles apart",length);
		}
		is_device = ( ! is_transformer && length < 0.01 ); // 60 feet minimum separation

		// // per-unit impedances
		extern double base_MVA;
		frompuZ = fromKV*fromKV/base_MVA;
		topuZ = toKV*toKV/base_MVA;
		
		// Generally accepted transformer parameters by rating

			// Dry-type 3-phase:
			//  <200 kVA   		r = 1.5 - 6.0 %
			//  200 - 500 kVA   r = 3.0 - 7.0 %
			//  500 - 750 kVA   r = 4.5 - 8.0 %
			//  >750 kVA        r = 5.0 - 8.0 %

			// Liquid-type 3-phase:
			//  <75 kVA         r = 1.0 - 4.5 %
			//	75 - 100 kVA	r = 1.0 - 5.0 %
			//	100 - 400 kVA	r = 1.2 - 6.0 %
			//	400 - 750 KVA	r = 1.5 - 7.0 %
			//	>750 kVA		r = 5.0 - 7.5 %	

			// Log fit for r:
			//	r = 0.03048*log(fromKV)-0.04209

			// Source: https://energycodeace.com/site/custom/public/reference-ace-t20/index.html#!Documents/gloss_specialimpedancetransformer.htm

			// X/R ratios
			// rating 	x/r  
			// 5		12
			// 10		15
			// 20		20
			// 50		30
			// 100		40
			// 200		50
			// 500		65

			// Log fit for x/r:
			//	x/r = max(5,26.8608*log(rating_MVA)-11.7491)
		
			// Source:        IEEE Std C37.010-2016

			//   b = 1/(r+jx)

		// Generally accepted device parameters

			// r = 0.001 Ohm
			// x = 0.010 Ohm
			// b = 1/(r+jx)

		if ( r == 0 && frompuZ > 0 )
		{
			if ( is_device )
			{
				// device, e.g., contactor
				r = 0.001/frompuZ; // 1 mOhm (?)
				verbose("device r is zero, autosize to default %.03lg pu.mOhm",r*1e3);
			}
			else if ( is_transformer )
			{
				// transformer
				r = (0.0348*log(fromKV)-0.04209)/frompuZ;
				verbose("transformer r is zero, autosize to default %.4lg pu.Ohm for %.1lf kV",r,fromKV);

			}
			else if ( length > 0 )
			{
				// power line
				double Imax = rateC / cos(autosize_angle);
				r = rateC / Imax / frompuZ;
				verbose("line r is zero, autosize for %.1lf A to %.4lg pu.Ohms for %.3lg kV %.1lf mile line",Imax,r,fromKV,length);
			}
		}
		
		if ( x == 0 && frompuZ > 0 )
		{
			if ( is_device )
			{
				// device, e.g., contactor
				x = 10*r; // x/r = 10 (?)
				verbose("device x is zero, autosize to default %.03lg pu.mOhm",x*1e3);
			}
			else if ( is_transformer )
			{
				// transformer
				x = r*max(26.8608*log(rateC/1e6)-11.7491,5.0);
				verbose("transformer x is zero, autosize to default %.4lg pu.Ohm for %.1lf MVA",x,rateC);
			}
			else if ( length > 0 )
			{
				// power line
				x = (-0.0008*fromKV+0.699)*length/frompuZ;
				verbose("line x is zero, autosize to %.4lg pu.Ohms for %.3lg kV %.1lf mile line",x,fromKV,length);
			}
		}

		if ( b == 0 && frompuZ > 0 )
		{
			if ( is_device )
			{
				// device, e.g., contactor
				verbose("device b is zero, no autosize available");
			}
			else if ( is_transformer )
			{
				// transformer
				verbose("transformer b is zero, no autosize available");
			}
			else if ( length > 0 )
			{
				// power line line-charging susceptance
				b = (-0.0002*fromKV+0.1122)*1e-6*length*frompuZ;
				verbose("b is zero, autosize to %.4lg pu.S for %.3lg kV %.1lf mile line",b,fromKV,length);
			}
		}
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
