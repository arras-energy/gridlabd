// module/pypower/shunt.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(shunt);
EXPORT_INIT(shunt);
EXPORT_PRECOMMIT(shunt);
EXPORT_SYNC(shunt);

CLASS *shunt::oclass = NULL;
shunt *shunt::defaults = NULL;

double shunt::minimum_voltage_magnitude_deadband = 0.002;
double shunt::minimum_voltage_angle_deadband = 0.01;

shunt::shunt(MODULE *module)
{
    if (oclass==NULL)
    {
        // register to receive notice for first top down. bottom up, and second top down synchronizations
        oclass = gld_class::create(module,"shunt",sizeof(shunt),PC_BOTTOMUP|PC_AUTOLOCK|PC_OBSERVER);
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
                PT_KEYWORD, "OFFLINE", enumeration(CS_OFFLINE),
                PT_KEYWORD, "ONLINE", enumeration(CS_ONLINE),
                PT_DESCRIPTION, "shunt status",

            PT_enumeration, "input", get_input_offset(),
                PT_KEYWORD, "ANGLE", enumeration(CI_ANGLE),
                PT_KEYWORD, "MAGNITUDE", enumeration(CI_MAGNITUDE),
                PT_DESCRIPTION, "voltage control input",

            PT_enumeration, "output", get_output_offset(),
                PT_DEFAULT,"REACTIVE",
                PT_KEYWORD, "REAL", enumeration(CO_REAL),
                PT_KEYWORD, "REACTIVE", enumeration(CO_REACTIVE),
                PT_DESCRIPTION, "voltage control output",

            PT_double, "voltage_high", get_voltage_high_offset(), 
                PT_REQUIRED,
                PT_DESCRIPTION, "controlled voltage upper limit",

            PT_double, "voltage_low", get_voltage_low_offset(),
                PT_REQUIRED,
                PT_DESCRIPTION, "controlled voltage lower limit",

            PT_object, "remote_bus", get_remote_bus_offset(),
                PT_DESCRIPTION, "remote bus name",

            PT_double, "admittance[MVAr]", get_admittance_offset(),
                PT_DESCRIPTION, "shunt admittance at unity voltage",

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

            PT_double, "dwell_time[s]", get_dwell_time_offset(),
                PT_DESCRIPTION, "control lockout",

            PT_double, "control_gain[MVAr/pu.V]", get_control_gain_offset(),
                PT_DESCRIPTION, "proportional feedback control gain",

            NULL)<1)
        {
                throw "unable to publish shunt properties";
        }

        gl_global_create("pypower::minimum_voltage_magnitude_deadband",
            PT_double, &minimum_voltage_magnitude_deadband, 
            PT_UNITS, "pu.kV",
            PT_DESCRIPTION, "Minimum deadband on voltage magnitude control",
        NULL);

        gl_global_create("pypower::minimum_voltage_angle_deadband",
            PT_double, &minimum_voltage_angle_deadband, 
            PT_UNITS, "deg",
            PT_DESCRIPTION, "Minimum deadband on voltage angle control",
        NULL);
    }
}

int shunt::create(void) 
{
    last_update = 0;
    last_delta = 0;
    return 1; /* return 1 on success, 0 on failure */
}

int shunt::init(OBJECT *parent)
{
    if ( control_mode > CM_CONTINUOUS_V )
    {
        error("advanced control modes not supported yet (use FIXED, DISCRETE_V, or CONTINUOUS_V)");
        return 0;
    }
    if ( control_mode != CM_FIXED && voltage_low >= voltage_high )
    {
        error("voltage_low is greater than voltage_high");
        return 0;
    }
    double control_deadband = input == CI_MAGNITUDE ? minimum_voltage_magnitude_deadband : minimum_voltage_angle_deadband;
    if ( control_deadband <= 0 )
    {
        error("minimum_voltage_{magnitude,angle}_deadband is not positive");
        return 0;
    }
    if ( control_mode != CM_FIXED && voltage_low > voltage_high - control_deadband )
    {
        error("voltage_low is within minimum_voltage_{magnitude,angle}_deadband of voltage_high");
        return 0;
    }

    if ( parent == NULL )
    {
        error("parent bus must be specified");
        return 0;
    }

    output_bus = (bus*)get_object(parent);
    if ( ! output_bus->isa("bus","pypower") )
    {
        error("parent is not a pypower bus");
        return 0;
    }
    if ( remote_bus == NULL )
    {
        remote_bus = parent;
    }

    input_bus = (bus*)get_object(remote_bus);
    if ( ! input_bus->isa("bus","pypower") )
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

    if ( dwell_time <= 0 )
    {
        error("dwell_time must be positive");
        return 0;
    }

    if ( control_mode == CM_CONTINUOUS_V && control_gain <= 0 )
    {
        error("control_gain (%g) must be positive for control_mode == CONTINUOUS_V",control_gain);
        return 0;
    }
    else if ( control_mode == CM_DISCRETE_V && steps_1 <= 0 )
    {
        error("steps_1 must be positive for control_mode == DISCRETE_V");
        return 0;
    }

    return 1;
}

TIMESTAMP shunt::precommit(TIMESTAMP t0)
{
    return update_control(t0); // control update
}

TIMESTAMP shunt::presync(TIMESTAMP t0)
{
    return TS_NEVER;
}

TIMESTAMP shunt::sync(TIMESTAMP t0)
{
    return update_control(t0,false); // time of next update
}

TIMESTAMP shunt::postsync(TIMESTAMP t0)
{
    return TS_NEVER;
}

void shunt::update_bus(void)
{
    verbose("update_bus()");
    if ( output == CO_REAL )
    {
        verbose("control output is REAL");
        output_bus->add_load(admittance,0);
    }
    else if ( output == CO_REACTIVE )
    {
        verbose("control output is REACTIVE");
        output_bus->add_load(admittance,-admittance);
        // output_bus->add_shunt(0,admittance);
    }
}

TIMESTAMP shunt::update_control(TIMESTAMP t0, bool update_time)
{
    TIMESTAMP t1 = TS_NEVER;
    verbose("update_control(t0=%s)",gld_clock(t0).get_string().get_buffer());
    verbose("input/output voltage magnitudes/angles are %lg%+lgj/%lg%+lgj respectively",input_bus->get_Vm(),input_bus->get_Va(),output_bus->get_Vm(),output_bus->get_Va());
    verbose("voltage input is %s",get_input() == CI_MAGNITUDE?"MAGNITUDE":"ANGLE");
    if ( status == CS_ONLINE && input_bus->get_Vm() > 1e-3 && output_bus->get_Vm() > 1e-3 )
    {
        bool control_ok = t0 >= last_update + dwell_time;
        if ( ! control_ok )
        {
            t1 = TIMESTAMP(last_update + dwell_time);
            last_delta = 0;
            verbose("voltage control is LOCKED until %s",gld_clock(t1).get_string().get_buffer());
        }
        else
        {           
            double V = get_input() == CI_MAGNITUDE ? input_bus->get_Vm() : input_bus->get_Va();
            bool Vhigh = V > voltage_high;
            bool Vlow = V < voltage_low;
            verbose("voltage check: %lg < %lg < %lg",voltage_low,V,voltage_high);
            if ( Vhigh ) verbose("voltage is high");
            if ( Vlow ) verbose("voltage is low");
            if ( control_mode == CM_DISCRETE_V ) 
            {
                // capacitors
                bool Alo = admittance <= 0;
                if ( Vhigh && Alo ) verbose("output is at minimum");
                bool Ahi = admittance >= admittance_1 * steps_1;
                if ( Vlow && Ahi ) verbose("output is at maximum");
                if ( Vlow && ! update_time )
                {
                    if ( Ahi )
                    {
                        warning("shunt voltage discrete control upper limit reached at %lg MVAr (V=%g)",admittance,V);
                        last_delta = 0;
                    }
                    else
                    {
                        last_update = t0;
                        admittance += admittance_1;
                        verbose("stepping up to %lg MVAr",admittance);
                        if ( last_delta < 0 )
                        {
                            warning("shunt voltage discrete control hunting at %lg MVAr (V=%g)",admittance,V);
                        }
                        last_delta = admittance_1;
                    }
                }
                else if ( Vhigh && ! update_time )
                {
                    if ( Alo )
                    {
                        warning("shunt voltage discrete control lower limit reached at %lg MVAr (V=%g)",admittance,V);
                        last_delta = 0;
                    }
                    else
                    {
                        admittance -= admittance_1;
                        last_update = t0;
                        verbose("stepping down to %lg MVAr",admittance);
                        if ( last_delta > 0 )
                        {
                            warning("shunt voltage discrete control hunting at %lg MVAr (V=%g)",admittance,V);
                        }
                        last_delta = -admittance_1;
                    }
                }
                else
                {
                    last_delta = 0;
                }
                t1 = TIMESTAMP(last_update + dwell_time);
            }
            else if ( control_mode == CM_CONTINUOUS_V )
            {
                // synchronous condensers
                if ( ! update_time )
                {
                    double Vref = V;
                    if ( Vlow )
                    {
                        Vref = Vlow;
                    }
                    else if ( Vhigh )
                    {
                        Vref = Vhigh;
                    }
                    double err = Vref - V;
                    last_delta = err * control_gain;
                    admittance += last_delta;
                    if ( admittance < -admittance_1 )
                    {
                        admittance = -admittance_1;
                        warning("shunt voltage continuous control lower limit reached at %lg MVAr (V=%g)",admittance,V);
                    }
                    else if ( admittance > admittance_1 )
                    {
                        admittance = admittance_1;
                        warning("shunt voltage continuous control upper limit reached at %lg MVAr (V=%g)",admittance,V);
                    }
                    else
                    {
                        verbose("setting admittance to %lg",admittance);
                    }
                }
                else
                {
                    last_delta = 0;
                }
                t1 = TIMESTAMP(last_update + dwell_time);
            }
            else
            {
                // fixed shunt has no dwell time
            }
        }
        update_bus();
    }
    else // offline
    {
        admittance = 0;
    }
    t1 = t1 <= t0 ? TS_NEVER : t1;
    verbose("update_control(t0=%s) -> %s",gld_clock(t0).get_string().get_buffer(),gld_clock(t1).get_string().get_buffer());
    return t1;
}
