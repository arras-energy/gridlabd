# module/pypower/Makefile.mk
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

pkglib_LTLIBRARIES += module/pypower/pypower.la

module_bus_bus_la_CPPFLAGS =
module_bus_bus_la_CPPFLAGS += $(AM_CPPFLAGS)

module_bus_bus_la_LDFLAGS =
module_bus_bus_la_LDFLAGS += $(AM_LDFLAGS)

module_bus_bus_la_LIBADD = 

module_bus_bus_la_SOURCES =
module_bus_bus_la_SOURCES += module/bus/main.cpp module/bus/pypower.h
module_bus_bus_la_SOURCES += module/bus/bus.cpp module/bus/bus.h
# module_bus_bus_la_SOURCES += module/bus/branch.cpp module/bus/branch.h
# module_bus_bus_la_SOURCES += module/bus/gen.cpp module/bus/gen.h
# module_bus_bus_la_SOURCES += module/bus/gencost.cpp module/bus/gencost.h
