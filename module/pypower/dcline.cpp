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
double dcline::default_loss0 = 0.0;
double dcline::default_loss1 = 0.05;

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
                PT_DEFAULT, "IN",
                PT_KEYWORD,"IN",(enumeration)DS_IN,
                PT_KEYWORD,"OUT",(enumeration)DS_OUT,
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

            PT_enumeration, "control", get_control_offset(),
                PT_DEFAULT, "TO",
                PT_KEYWORD, "FROM", (enumeration)CP_FROM,
                PT_KEYWORD, "TO", (enumeration)CP_TO,
                PT_DESCRIPTION, "Control point at which power flow is regulated",

            NULL) < 1 )
        {
            throw "unable to publish dcline properties";
        }

        gl_global_create("pypower::default_dcline_loss0",
            PT_double, &default_loss0, 
            PT_UNITS, "MW",
            PT_DESCRIPTION, "Default DC line power loss constant",
            NULL);

        gl_global_create("pypower::default_dcline_loss1",
            PT_double, &default_loss1, 
            PT_UNITS, "MW/MW",
            PT_DESCRIPTION, "Default DC line power loss factor",
            NULL);
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

    set_control(CP_TO);

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

    double loss = calculate_loss(loss0);
    if ( Sfrom.r > 0 && Sto.r > 0 )
    {
        if ( loss1 == 0 )
        {
            loss1 = loss;
        }
        else if ( fabs(loss1-loss) > 1e-6 )
        {
            warning("specified loss function Sto=%.6lg*Sfrom%+.6lg is inconsistent with Sfrom=%.6lg%+.6lgj and Sto=%.6lg%+.6lgj, fixing line output",
                loss1,loss0,Sfrom.r,Sfrom.i,Sto.r,Sto.i);
            update();
        }
    }
    else if ( loss1 == 0 )
    {
        warning("loss1 is not specified and cannot be inferred from initial values of Sfrom and Sto, using default %.6lg*S%+.6lg loss",
            default_loss1,default_loss0);
        loss0 = default_loss0;
        loss1 = default_loss1;
    }
    else
    {
        update();
    }

    return 1;
}

void dcline::update(void)
{
    if ( status == DS_OUT )
    {
        Sfrom = 0.0;
        Sto = 0.0;
    }
    else if ( control == CP_TO )
    {
        update_from();
    }
    else
    {
        update_to();
    }
}

void dcline::update_from(void)
{
    Sfrom = Sto/(1-loss1) + loss0;
    Sfrom.r = min(max(Pmin,Sfrom.r),Pmax);
    Sfrom.i = min(max(Qminf,Sfrom.i),Qmaxf);
    Sto = Sfrom*(1-loss1) - loss0;
}

void dcline::update_to(void)
{
    Sto = Sfrom*(1-loss1) - loss0;
    Sto.r = min(max(Pmin,Sto.r),Pmax);
    Sto.i = min(max(Qminf,Sto.i),Qmaxf);
    Sfrom = Sto/(1-loss1) + loss0;
}

double dcline::calculate_loss(double constant)
{
    if ( Sto.r < Sfrom.r )
    {
        return (Sto.r+constant)/Sfrom.r;
    }
    else if ( Sfrom.r < Sto.r )
    {
        return (Sfrom.r+constant)/Sto.r;
    }
    else
    {
        return loss1;
    }
}

TIMESTAMP dcline::precommit(TIMESTAMP t0)
{
    update();
    return TS_NEVER;
}

