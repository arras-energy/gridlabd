// module/pypower/shunt.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(shunt);
EXPORT_INIT(shunt);
EXPORT_SYNC(shunt);

CLASS *shunt::oclass = NULL;
shunt *shunt::defaults = NULL;

double shunt::minimum_voltage_deadband = 0.002;

shunt::shunt(MODULE *module)
{
    if (oclass==NULL)
    {
        // register to receive notice for first top down. bottom up, and second top down synchronizations
        oclass = gld_class::create(module,"shunt",sizeof(shunt),PC_PRETOPDOWN|PC_BOTTOMUP|PC_AUTOLOCK|PC_OBSERVER);
        if (oclass==NULL)
            throw "unable to register class shunt";
        else
            oclass->trl = TRL_PROTOTYPE;

        defaults = this;
        if (gl_publish_variable(oclass,

            PT_enumeration, "control_mode", get_control_mode_offset(),
                PT_KEYWORD, "FIXED", enumeration(CM_FIXED),
                PT_KEYWORD, "DISCRETE_V", enumeration(CM_DISCRETE_V),
                PT_KEYWORD, "CONTINUOUS_V", enumeration(CM_CONTINUOUS_V),
                PT_KEYWORD, "DISCRETE_VAR", enumeration(CM_DISCRETE_VAR),
                PT_KEYWORD, "DISCRETE_VSC", enumeration(CM_DISCRETE_VSC),
                PT_KEYWORD, "DISCRETE_Y", enumeration(CM_DISCRETE_Y),
                PT_DESCRIPTION, "shunt control mode",

            PT_enumeration, "status", get_status_offset(),
                PT_KEYWORD, "OFFLINE", enumeration(S_OFFLINE),
                PT_KEYWORD, "ONLINE", enumeration(S_ONLINE),
                PT_DESCRIPTION, "shunt status",

            PT_double, "voltage_high[pu]", get_voltage_high_offset(), 
                PT_DEFAULT, "1 pu",
                PT_DESCRIPTION, "controlled voltage upper limit",

            PT_double, "voltage_low[pu]", get_voltage_low_offset(),
                PT_DEFAULT, "1 pu",
                PT_DESCRIPTION, "controlled voltage lower limit",

            PT_object, "remote_bus", get_remote_bus_offset(),
                PT_DESCRIPTION, "remote bus name",

            PT_double, "admittance[MVAr]", get_admittance_offset(),
                PT_DESCRIPTION, "shunt admittance at unity voltage",

            PT_bool, "real", get_real_offset(),
                PT_DESCRIPTION, "admittance is real (not reactive)",

            PT_int32, "steps_1", get_steps_1_offset(),
                PT_DESCRIPTION, "numbers of steps in control block 1",

            PT_double, "admittance_1[MVAr]", get_admittance_1_offset(),
                PT_DESCRIPTION, "control block 1 shunt admittance step at unity voltage",

            PT_int32, "steps_2", get_steps_2_offset(),
                PT_DESCRIPTION, "number of steps in control block 2",

            PT_double, "admittance_2[MVAr]", get_admittance_2_offset(),
                PT_DESCRIPTION, "control block 2 shunt admittance step at unity voltage",

            PT_int32, "steps_3", get_steps_3_offset(),
                PT_DESCRIPTION, "number of steps in control block 3",

            PT_double, "admittance_3[MVAr]", get_admittance_3_offset(),
                PT_DESCRIPTION, "control block 3 shunt admittance step at unity voltage",

            PT_int32, "steps_4", get_steps_4_offset(),
                PT_DESCRIPTION, "number of steps in control block 4",

            PT_double, "admittance_4[MVAr]", get_admittance_4_offset(),
                PT_DESCRIPTION, "control block 4 shunt admittance step at unity voltage",

            PT_int32, "steps_5", get_steps_5_offset(),
                PT_DESCRIPTION, "number of steps in control block 5",

            PT_double, "admittance_5[MVAr]", get_admittance_5_offset(),
                PT_DESCRIPTION, "control block 5 shunt admittance step at unity voltage",

            PT_int32, "steps_6", get_steps_6_offset(),
                PT_DESCRIPTION, "number of steps in control block 6",

            PT_double, "admittance_6[MVAr]", get_admittance_6_offset(),
                PT_DESCRIPTION, "control block 6 shunt admittance step at unity voltage",

            PT_int32, "steps_7", get_steps_7_offset(),
                PT_DESCRIPTION, "number of steps in control block 7",

            PT_double, "admittance_7[MVAr]", get_admittance_7_offset(),
                PT_DESCRIPTION, "control block 7 shunt admittance step at unity voltage",

            PT_int32, "steps_8", get_steps_8_offset(),
                PT_DESCRIPTION, "number of steps in control block 8",

            PT_double, "admittance_8[MVAr]", get_admittance_8_offset(),
                PT_DESCRIPTION, "control block 8 shunt admittance step at unity voltage",

            NULL)<1)
        {
                throw "unable to publish shunt properties";
        }

        gl_global_create("pypower::minimum_voltage_deadband",
            PT_double, &minimum_voltage_deadband, 
            PT_UNITS, "pu",
            PT_DESCRIPTION, "Minimum deadband on voltage control",

        NULL);
    }
}

int shunt::create(void) 
{
    return 1; /* return 1 on success, 0 on failure */
}

int shunt::init(OBJECT *parent)
{
    if ( control_mode > CM_DISCRETE_V )
    {
        error("advanced control modes not supported yet (use FIXED or DISCRETE_V)");
        return 0;
    }
    if ( control_mode != CM_FIXED && voltage_low > voltage_high )
    {
        error("voltage_low is greater than voltage_high");
        return 0;
    }
    if ( control_mode != CM_FIXED && voltage_low > voltage_high - minimum_voltage_deadband )
    {
        error("voltage_low is within minimum_voltage_deadband of voltage_high");
        return 0;
    }
    if ( parent == NULL )
    {
        error("parent bus must be specified");
        return 0;
    }
    output = (bus*)get_object(parent);
    if ( ! output->isa("bus","pypower") )
    {
        error("parent is not a pypower bus");
        return 0;
    }
    if ( remote_bus == NULL )
    {
        remote_bus = parent;
    }
    input = (bus*)get_object(remote_bus);
    if ( ! input->isa("bus","pypower") )
    {
        error("remote_bus is not a pypower bus");
        return 0;
    }
    if ( steps_1 > 0 && admittance_1 == 0 )
    {
        error("zero admittance step values are not valid for active control blocks");
        return 0;
    }
    if ( steps_2 > 0 || steps_3 > 0 || steps_4 > 0 || steps_5 > 0 || steps_6 > 0 || steps_7 > 0 || steps_8 > 0 )
    {
        error("multiple control blocks not supported yet (steps_[2-8] > 0)");
        return 0;
    }
    return 1;
}

TIMESTAMP shunt::presync(TIMESTAMP t0)
{
    update(t0,false); // bus data update
    return TS_NEVER;
}

TIMESTAMP shunt::sync(TIMESTAMP t0)
{
    return update(t0,true); // control update
}

TIMESTAMP shunt::postsync(TIMESTAMP t0)
{
    return TS_NEVER;
}

void shunt::push_admittance(void)
{
    if ( real )
    {
        output->add_shunt(admittance,0);
    }
    else
    {
        output->add_shunt(0,admittance);
    }
}

TIMESTAMP shunt::update(TIMESTAMP t0,bool control)
{
    if ( status == S_ONLINE )
    {
        if ( control )
        {
            if ( control_mode == CM_DISCRETE_V )
            {
                double Vm = input->get_Vm();
                //debug("input voltage is %.3lf pu (Vmin=%.3lf, Vmax=%.3lf)",Vm,voltage_low,voltage_high);
                bool Vhigh = Vm > voltage_high;
                bool Vlow = Vm < voltage_low;
                bool Alo = admittance <= 0;
                bool Ahi = admittance >= admittance_1 * steps_1;
                bool Amax = admittance_1 > 0 ? Ahi : Alo ;
                bool Amin = admittance_1 > 0 ? Alo : Ahi;
                // debug("admittance_1=%lf, steps_1=%d, admittance=%lf; %s %s %s %s",
                //     admittance_1, steps_1, admittance,
                //     Vhigh?"Vhigh":"!Vhigh",Vlow?"Vlow":"!Vlow",Amax?"Amax":"!Amax",Amin?"Amin":"!Amin");
                if ( ( Vlow && ! Amax ) || ( Vhigh && ! Amin ) )
                {
                    if ( control )
                    {
                        admittance += admittance_1;
                        output->add_shunt(real?admittance_1:0,real?0:admittance_1);
                        debug("stepping up admittance to %.1lf MVAr",admittance);
                    }
                    return t0;
                }
                else if ( ( Vlow && Amax ) || ( Vhigh && Amin ) )
                {
                    if ( control )
                    {
                        warning("shunt voltage control limit reached at %lf MVAr",admittance);
                    }
                }
                if ( ( Vhigh && ! Amin ) || ( Vlow && ! Amax ) )
                {
                    if ( control )
                    {
                        admittance -= admittance_1;
                        output->add_shunt(real?-admittance_1:0,real?0:-admittance_1);
                        debug("stepping down admittance to %.1lf MVAr",admittance);
                    }
                    return t0;
                }
                else if ( ( Vhigh && Amin ) || ( Vlow && Amax ) )
                {
                    if ( control )
                    {
                        warning("shunt voltage control limit reached at %lf MVAr",admittance);
                    }
                }
            }
        }
        else
        {
            debug("adding bus admittance %.1lf MVAr",admittance);
            push_admittance();            
        }
    }
    return TS_NEVER;
}
