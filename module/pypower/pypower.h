// module/pypower/pypower.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_H
#define _PYPOWER_H

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <math.h>

#include "gridlabd.h"

#include "bus.h"
#include "branch.h"
#include "gen.h"
#include "gencost.h"
#include "load.h"
#include "powerplant.h"
#include "powerline.h"
#include "relay.h"
#include "scada.h"
#include "transformer.h"

#define MAXENT 30000 // maximum number of bus/branch/gen/gencost entities supported

#endif
