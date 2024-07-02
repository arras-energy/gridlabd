// module/behavior/behavior.h
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#ifndef _PYPOWER_H
#define _PYPOWER_H

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <math.h>

#include "gridlabd.h"

#include "learning.h"
#include "random.h"
#include "system.h"

void add_system(class system *);

#endif
