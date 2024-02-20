# module/pypower/Makefile.mk
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

pkglib_LTLIBRARIES += module/pypower/pypower.la

module_pypower_pypower_la_CPPFLAGS =
module_pypower_pypower_la_CPPFLAGS += $(AM_CPPFLAGS)

module_pypower_pypower_la_LDFLAGS =
module_pypower_pypower_la_LDFLAGS += $(AM_LDFLAGS)

module_pypower_pypower_la_LIBADD = 

module_pypower_pypower_la_SOURCES =
module_pypower_pypower_la_SOURCES += module/pypower/pypower.cpp module/pypower/pypower.h
module_pypower_pypower_la_SOURCES += module/pypower/bus.cpp module/pypower/bus.h
module_pypower_pypower_la_SOURCES += module/pypower/branch.cpp module/pypower/branch.h
module_pypower_pypower_la_SOURCES += module/pypower/gen.cpp module/pypower/gen.h
module_pypower_pypower_la_SOURCES += module/pypower/gencost.cpp module/pypower/gencost.h

dist_pkgdata_DATA += module/pypower/pypower_solver.py
