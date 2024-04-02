// module/behavior/behavior.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#define DLMAIN

#include "behavior.h"

EXPORT CLASS *init(CALLBACKS *fntable, MODULE *module, int argc, char *argv[])
{
    if (set_callback(fntable)==NULL)
    {
        errno = EINVAL;
        return NULL;
    }

    INIT_MMF(behavior);

    new class random(module);
    new class system(module);

    // always return the first class registered
    return random::oclass;
}

class system **system_list = NULL;
size_t n_systems = 0;
size_t n_groups = 0;
void add_system(class system *sys)
{
    system_list = (class system**)realloc(system_list,sizeof(*system_list)*(n_systems+1));
    system_list[n_systems++] = sys;
}

static int group(int *groups, enumeration type, int n=-1)
{
    if ( n == -1 )
    {
        n_groups = 0;
        for ( size_t n = 0 ; n < n_systems ; n++ )
        {
            if ( groups[n] == -1 )
            {
                groups[n] = group(groups,type,n);
            }
            fprintf(stderr,"type %d group[%lu] = %d\n",int(type),n,groups[n]);
        }
        return n_groups;
    }
    else if ( groups[n] >= 0 )
    {
        return groups[n];
    }

    class system *sys = system_list[n];
    if ( groups[n] == -1 )
    {
        if ( sys->get_connection() != NULL && sys->get_connection_type() == type )
        {
            groups[n] = group(groups,type,sys->group_id);
            return groups[n];
        }
        else
        {
            groups[n] = sys->group_id = n_groups++;
            return groups[n];
        }
    }
    else
    {
        return groups[n];
    }

}

EXPORT TIMESTAMP on_precommit(TIMESTAMP t0)
{
    int t_groups[n_systems];
    memset(t_groups,-1,sizeof(t_groups[0])*n_systems);
    group(t_groups,system::VALUE);

    int m_groups[n_systems];
    memset(m_groups,-1,sizeof(m_groups[0])*n_systems);
    group(m_groups,system::ASSET);

    double C = 0;
    double N = 0;
    double M = 0;
    double T = 0;
    for ( size_t n = 0 ; n < n_systems ; n++ )
    {
        class system *sys = system_list[n];
        fprintf(stderr,"system %lu: Cp = %g, N = %lld\n",n,sys->get_Cp(),sys->get_N());
        C += sys->get_Cp();
        N += sys->get_N();
    }
    for ( size_t n = 0 ; n < n_systems ; n++ )
    {
        class system *sys = system_list[n];
        fprintf(stderr,"system %lu: T = %g, M = %g\n",n,sys->get_tau(),sys->get_mu());
        T += sys->get_Cp() / C * sys->get_tau();
        M += sys->get_N() / N * sys->get_mu();
    }
    fprintf(stderr,"C = %g, T = %g, M = %g\n",C,T,M);
    for ( size_t n = 0 ; n < n_systems ; n++ )
    {
        class system *sys = system_list[n];
        sys->set_tau(T);
        sys->set_mu(M);
        sys->update();
    }
    return TS_NEVER;
}

EXPORT int do_kill(void*)
{
    // if global memory needs to be released, this is a good time to do it
    return 0;
}

EXPORT int check(){
    // if any assert objects have bad filenames, they'll fail on init()
    return 0;
}
