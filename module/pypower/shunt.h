// module/pypower/shun t.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_SHUNT_H
#define _PYPOWER_SHUNT_H

#include "gridlabd.h"

class shunt : public gld_object 
{

public:

    // enumerations
    typedef enum {
        CM_FIXED = 0,
        CM_DISCRETE_V = 1,
        CM_CONTINUOUS_V = 2,
        CM_DISCRETE_VAR = 3,
        CM_DISCRETE_VSC = 4,
        CM_DISCRETE_Y = 5,
    } CONTROLMODE;

    typedef enum {
        CS_OFFLINE = 0,
        CS_ONLINE = 1,
    } STATUS;

    typedef enum {
        CI_MAGNITUDE = 0,
        CI_ANGLE = 1,
    } CONTROLINPUT;

    typedef enum {
        CO_REACTIVE = 0,
        CO_REAL = 1,
    } CONTROLOUTPUT;

public:

    // module globals
    static double minimum_voltage_magnitude_deadband;
    static double minimum_voltage_angle_deadband;

public:

    // published properties
    GL_ATOMIC(enumeration,control_mode);
    GL_ATOMIC(enumeration,status);
    GL_ATOMIC(enumeration,input);
    GL_ATOMIC(enumeration,output);    
    GL_ATOMIC(double,voltage_high);
    GL_ATOMIC(double,voltage_low);
    GL_ATOMIC(object,remote_bus);
    GL_ATOMIC(double,admittance);
    GL_ATOMIC(int32,steps_1);
    GL_ATOMIC(double,admittance_1);
    GL_ATOMIC(int32,steps_2);
    GL_ATOMIC(double,admittance_2);
    GL_ATOMIC(int32,steps_3);
    GL_ATOMIC(double,admittance_3);
    GL_ATOMIC(int32,steps_4);
    GL_ATOMIC(double,admittance_4);
    GL_ATOMIC(int32,steps_5);
    GL_ATOMIC(double,admittance_5);
    GL_ATOMIC(int32,steps_6);
    GL_ATOMIC(double,admittance_6);
    GL_ATOMIC(int32,steps_7);
    GL_ATOMIC(double,admittance_7);
    GL_ATOMIC(int32,steps_8);
    GL_ATOMIC(double,admittance_8);
    GL_ATOMIC(double,dwell_time);
    GL_ATOMIC(double,control_gain);

private:

    // internal variables
    bus *input_bus;
    bus *output_bus;
    TIMESTAMP last_update;

private:
    TIMESTAMP update_control(TIMESTAMP t0,bool update_time=false);
    void update_bus(void);

public:

    // event handlers
    shunt(MODULE *module);
    int create(void);
    int init(OBJECT *parent);
    TIMESTAMP precommit(TIMESTAMP t0);
    TIMESTAMP presync(TIMESTAMP t0);
    TIMESTAMP sync(TIMESTAMP t0);
    TIMESTAMP postsync(TIMESTAMP t0);

public:

    // internal properties
    static CLASS *oclass;
    static shunt *defaults;
};

#endif // _PYPOWER_SHUNT_H
