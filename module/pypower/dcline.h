// module/pypower/dcline.h
// Copyright (C) 2025 Eudoxys Sciences LLC

#ifndef _PYPOWER_DCLINE_H
#define _PYPOWER_DCLINE_H

#include "gridlabd.h"

class dcline : public gld_object
{
public:

    static size_t ndcline;
    static dcline *dclinelist[MAXENT];
    static double default_loss0;
    static double default_loss1;

public:

    // properties
    GL_ATOMIC(object,from);
    GL_ATOMIC(object,to);
    GL_ATOMIC(int32,fbus);
    GL_ATOMIC(int32,tbus);
    typedef enum {DS_OUT=0,DS_IN=1} DCLINESTATUS;
    GL_ATOMIC(enumeration,status);
    GL_ATOMIC(complex,Sfrom);
    GL_ATOMIC(complex,Sto);
    GL_ATOMIC(double,Vfrom);
    GL_ATOMIC(double,Vto);
    GL_ATOMIC(double,Pmin);
    GL_ATOMIC(double,Pmax);
    GL_ATOMIC(double,Qminf);
    GL_ATOMIC(double,Qmaxf);
    GL_ATOMIC(double,Qmint);
    GL_ATOMIC(double,Qmaxt);
    GL_ATOMIC(double,loss0);
    GL_ATOMIC(double,loss1);

    GL_ATOMIC(double,mu_Pmin);
    GL_ATOMIC(double,mu_Pmax);
    GL_ATOMIC(double,mu_Qminf);
    GL_ATOMIC(double,mu_Qmaxf);
    GL_ATOMIC(double,mu_Qmint);
    GL_ATOMIC(double,mu_Qmaxt);

    typedef enum {
        CP_SINK=0,
        CP_SOURCE=1,
        CP_TO=2,
        CP_FROM=3,
    } CONTROLPOINT;
    GL_ATOMIC(enumeration,control);

public:

    void update(void);
    void update_from(void);
    void update_to(void);
    double calculate_loss(double constant=0);

public:

    // event handlers
    dcline(MODULE *module);
    int create(void);
    int init(OBJECT *parent);
    TIMESTAMP precommit(TIMESTAMP t0);

public:

    // internal properties
    static CLASS *oclass;
    static dcline *defaults;
};

#endif // _PYPOWER_DCLINE_H
