// module/optimize/cvx.h

#ifndef _CVX_H
#define _CVX_H

#include "gridlabd.h"

#define OE_NONE ((set)0x00)
#define OE_PRECOMMIT ((set)0x01)
#define OE_COMMIT ((set)0x02)

class cvx : public gld_object
{

public:

    // data types

public:

    // published properties
    GL_ATOMIC(set,event);

private:

    // private properties
    // TODO

public:

    // required implementations
    cvx(MODULE *module);
    int create(void);
    int init(OBJECT *parent);

public:

    static CLASS *oclass;
    static cvx *defaults;

};

#endif // _CVX_H
