// module/optimize/cvx.h

#ifndef _CVX_H
#define _CVX_H

#include "gridlabd.h"

// method declarations
DECL_METHOD(cvx,data);
DECL_METHOD(cvx,variables);
DECL_METHOD(cvx,objective);
DECL_METHOD(cvx,constraints);

class cvx : public gld_object
{

public: // module globals

    typedef enum {
        BE_CPP = 0,
        BE_SCIPY = 1,
        BE_NUMPY =2,
    } BACKENDTYPE;
    static enumeration backend;

    // typedef enum {
    //     CO_NONE        = 0x00,
    //     CO_VERBOSE     = 0x01,
    //     CO_GP          = 0x02,
    //     CO_QCP         = 0x04,
    //     CO_GRADIENTS   = 0x08,
    //     CO_DPPIGNORE   = 0x10,
    //     CO_DPPENFORCE  = 0x20,
    // } OPTIONS;
    // static set options;

    // typedef enum {
    //     CS_AUTO        = 0,
    //     CS_CLARABEL    = 1,
    //     CS_CBC         = 2,
    //     CS_COPT        = 3,
    //     CS_DAQP        = 4,
    //     CS_GLOP        = 5,
    //     CS_GLPK        = 6,
    //     CS_GLPK_MI     = 7,
    //     CS_OSQP        = 8,
    //     CS_PIQP        = 9,
    //     CS_PROXQP      = 10,
    //     CS_PDLP        = 12,
    //     CS_CPLEX       = 13,
    //     CS_NAG         = 14,
    //     CS_ECOS        = 15,
    //     CS_GUROBI      = 16,
    //     CS_MOSEK       = 17,
    //     CS_CVXOPT      = 18,
    //     CS_DSPA        = 19,
    //     CS_SCS         = 20,
    //     CS_SCIP        = 21,
    //     CS_XPRESS      = 22,
    //     CS_SCIPY       = 23,
    //     _CS_LAST = CS_SCIPY,
    //     CS_CUSTOM      = -1,
    // } SOLVER;
    // static enumeration solver;

    // static char1024 custom_solver;

    // static bool warm_start;

    // static char1024 solver_options;

    typedef enum {
        OF_HALT = 0,
        OF_WARN = 1,
        OF_IGNORE = 2,
    } ONFAILURE;
    static enumeration failure_handling;

    static char1024 imports;

    static char1024 problemdump;

public: // public properties
    
    typedef enum {
        OE_NONE      = 0x00,
        OE_INIT      = 0x01,
        OE_PRECOMMIT = 0x02,
        OE_PRESYNC   = 0x04,
        OE_SYNC      = 0x08,
        OE_POSTSYNC  = 0x10,
        OE_COMMIT    = 0x20,
        OE_FINALIZE  = 0x40,
    } OPTIMIZATIONEVENT;
    GL_BITFLAGS(set,event);
    GL_STRING(char1024,presolve);
    GL_STRING(char1024,postsolve);
    GL_STRING(char1024,on_failure);
    GL_STRING(char1024,on_exception);
    GL_STRING(char1024,on_infeasible);
    GL_STRING(char1024,on_unbounded);
    GL_ATOMIC(double,value);

    GL_METHOD(cvx,objective);
    GL_METHOD(cvx,data);
    GL_METHOD(cvx,variables);
    GL_METHOD(cvx,constraints);
    GL_STRING(char1024,solver_options);

private: // private properties
    
    static PyObject *main_module;
    static PyObject *globals;

    typedef struct s_reference {
        double *ref;
        struct s_reference* next;
    } REFERENCE;
    typedef struct s_data {
        char *spec;
        char *name;
        REFERENCE *data;
        PyObject *list;
        struct s_data *next;
    } DATA;
    typedef struct s_variable {
        char *spec;
        char *name;
        REFERENCE *primal;
        REFERENCE *dual;
        size_t count;
        struct s_variable *next;
    } VARIABLE;
    typedef struct s_constraint {
        char *spec;
        struct s_constraint *next;
    } CONSTRAINT;
    struct s_problem {
        char *objective;
        DATA *data;
        VARIABLE *variables;
        CONSTRAINT *constraints;
    } problem;

    PyObject *cvxpy; // cvxpy module

public: // required methods

    cvx(MODULE *module);
    int create(void);
    int init(OBJECT *parent);

public: // event handlers

    int precommit(TIMESTAMP t0);
    TIMESTAMP presync(TIMESTAMP t0);
    TIMESTAMP sync(TIMESTAMP t0);
    TIMESTAMP postsync(TIMESTAMP t0);
    TIMESTAMP commit(TIMESTAMP t0,TIMESTAMP t1);
    int finalize(void);

private: // private methods

    bool add_data(struct s_problem &problem, const char *value);
    bool add_variables(struct s_problem &problem, const char *value);
    bool add_constraints(struct s_problem &problem, const char *value);
    bool set_objective(struct s_problem &problem, const char *value);
    bool update_solution(struct s_problem &problem);

public: // required members

    static CLASS *oclass;
    static cvx *defaults;

};

#endif // _CVX_H