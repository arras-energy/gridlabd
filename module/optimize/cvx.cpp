// module/optimize/cvx.cpp

#include "cvx.h"

EXPORT_CREATE(cvx);
EXPORT_INIT(cvx);

CLASS *cvx::oclass = NULL;
cvx *cvx::defaults = NULL;

cvx::cvx(MODULE *module)
{
    if (oclass==NULL)
    {
        // register to receive notice for first top down. bottom up, and second top down synchronizations
        oclass = gld_class::create(module,"cvx",sizeof(cvx),PC_AUTOLOCK|PC_OBSERVER);
        if (oclass==NULL)
            throw "unable to register class cvx";
        else
            oclass->trl = TRL_PROVEN;

        defaults = this;
        if (gl_publish_variable(oclass,

            PT_set, "event", get_event_offset(),
                PT_DEFAULT, "NONE",
                PT_KEYWORD, "COMMIT", OE_COMMIT,
                PT_KEYWORD, "PRECOMMIT", OE_PRECOMMIT,
                PT_KEYWORD, "NONE", OE_NONE,
                PT_DESCRIPTION, "event during which the optimization problem should be solved",

            NULL)<1)
        {
            exception("unable to publish optimize/cvx properties");
        }
    }
}

int cvx::create(void) 
{
    // TODO
    return 1; /* return 1 on success, 0 on failure */
}

int cvx::init(OBJECT *parent)
{
    // TODO
    return 1;
}

