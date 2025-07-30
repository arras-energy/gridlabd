// module/pypower/dcline.cpp
// Copyright (C) 2025 Eudoxys Sciences LLC

#include "pypower.h"

EXPORT_CREATE(dcline)
EXPORT_INIT(dcline)
EXPORT_PRECOMMIT(dcline)

CLASS *dcline::oclass = NULL;
dcline *dcline::defaults = NULL;

size_t dcline::ndcline = 0;
dcline *dcline::dclinelist[MAXENT];

dcline::dcline(MODULE *module)
{
    if ( oclass == NULL )
    {
        oclass = gld_class::create(module,"dcline",sizeof(dcline),PC_AUTOLOCK|PC_OBSERVER);
        if ( oclass == NULL )
        {
            throw "unable to register class dcline";
        }
        else
        {
            oclass->trl = TRL_PROVEN;
        }
        defaults = this;
        if ( gl_publish_variable(oclass,

            PT_object, "from", get_from_offset(),
                PT_REQUIRED,
                PT_DESCRIPTION, "'from' bus name",

            PT_object, "to", get_to_offset(),
                PT_REQUIRED,
                PT_DESCRIPTION, "'to' bus name",

            PT_int32, "fbus", get_fbus_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "'from' bus number",

            PT_int32, "tbus", get_tbus_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "'to' bus number",

            PT_enumeration, "status", get_status_offset(),
                PT_KEYWORD,"OUT",(enumeration)DS_OUT,
                PT_KEYWORD,"IN",(enumeration)DS_IN,
                PT_DEFAULT, "IN",
                PT_DESCRIPTION, "initial branch status, IN=1 - in service, OUT=0 - out of service",

            PT_complex, "Sfrom[MVA]", get_Sfrom_offset(),
                PT_REQUIRED,
                PT_DESCRIPTION, "MVA flow in at 'from' bus",

            PT_complex, "Sto[MVA]", get_Sto_offset(),
                PT_REQUIRED,
                PT_DESCRIPTION, "MW flow in at 'to' bus",

            PT_double, "Vfrom[pu.V]", get_Vfrom_offset(),
                PT_DEFAULT, "1 pu.V",
                PT_DESCRIPTION, "voltage setpoint at 'from' bus (p.u.)",

            PT_double, "Vto[pu.V]", get_Vto_offset(),
                PT_DEFAULT, "1 pu.V",
                PT_DESCRIPTION, "voltage setpoint at  'to'  bus (p.u.)",

            PT_double, "Pmin[MW]", get_Pmin_offset(),
                PT_DESCRIPTION, "lower limit on PF (MW flow at 'from' end)",

            PT_double, "Pmax[MW]", get_Pmax_offset(),
                PT_DESCRIPTION, "upper limit on PF (MW flow at 'from' end)",

            PT_double, "Qminf[MVAr]", get_Qminf_offset(),
                PT_DESCRIPTION, "lower limit on MVAr injection at 'from' bus",

            PT_double, "Qmaxf[MVAr]", get_Qmaxf_offset(),
                PT_DESCRIPTION, "upper limit on MVAr injection at 'from' bus",

            PT_double, "Qmint[MVAr]", get_Qmint_offset(),
                PT_DESCRIPTION, "lower limit on MVAr injection at  'to'  bus",

            PT_double, "Qmaxt[MVAr]", get_Qmaxt_offset(),
                PT_DESCRIPTION, "upper limit on MVAr injection at  'to'  bus",

            PT_double, "loss0[MW]", get_loss0_offset(),
                PT_DESCRIPTION, "constant term of linear loss function (MW) on Sfrom",

            PT_double, "loss1[MW/MW]", get_loss1_offset(),
                PT_DESCRIPTION, "linear term of linear loss function (MW/MW) w.r.t Sfrom",

            PT_double, "mu_Pmin[$/MW]", get_mu_Pmin_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower flow limit at 'from' bus",

            PT_double, "mu_Pmax[$/MW]", get_mu_Pmax_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper flow limit at 'from' bus",

            PT_double, "mu_Qminf[$/MW]", get_mu_Qminf_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower VAr limit at 'from' bus",

            PT_double, "mu_Qmaxf[$/MW]", get_mu_Qmaxf_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper VAr limit at 'from' bus",

            PT_double, "mu_Qmint[$/MW]", get_mu_Qmint_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "Kuhn-Tucker multiplier on lower VAr limit at 'to' bus",

            PT_double, "mu_Qmaxt[$/MW]", get_mu_Qmaxt_offset(),
                PT_OUTPUT,
                PT_DESCRIPTION, "Kuhn-Tucker multiplier on upper VAr limit at 'to' bus",

            NULL) < 1 )
        {
            throw "unable to publish dcline properties";
        }
    }
}

int dcline::create(void)
{
    if ( ndcline < MAXENT )
    {
        dclinelist[ndcline++] = this;
    }
    else
    {
        throw "maximum dcline entities exceeded";
    }

    set_from("");
    set_to("");
    set_fbus(0);
    set_tbus(0);
    set_status(DS_IN);
    set_Sfrom(0.0);
    set_Sto(0.0);
    set_Vfrom(1.0);
    set_Vto(1.0);
    set_Pmin(0.0);
    set_Pmax(0.0);
    set_Qminf(0.0);
    set_Qmaxf(0.0);
    set_Qmint(0.0);
    set_Qmaxt(0.0);
    set_loss0(0.0);
    set_loss1(0.0);
    
    set_mu_Pmin(0.0);
    set_mu_Pmax(0.0);
    set_mu_Qminf(0.0);
    set_mu_Qmaxf(0.0);
    set_mu_Qmint(0.0);
    set_mu_Qmaxt(0.0);

    return 1;
}

int dcline::init(OBJECT *parent)
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

    return 1;
}

TIMESTAMP dcline::precommit(TIMESTAMP t0)
{
    // power flow is determine to by "load" side
    complex &load = ( Sto.r < 0 ? Sto : Sfrom );
    complex &gen = ( Sto.r > 0 ? Sto : Sfrom );
    load.i = min(max(Qmint,load.i),Qmaxt);
    // logic: gen = load + loss1*gen + loss0
    load =  ( gen + loss0 ) / (1 + loss1);
    gen.r = min(max(Pmin,gen.r),Pmax);
    gen.i = min(max(Qminf,gen.i),Qmaxf);
    return TS_NEVER;
}

