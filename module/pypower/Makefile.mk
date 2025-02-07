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

module_pypower_pypower_la_SOURCES += module/pypower/branch.cpp module/pypower/branch.h
module_pypower_pypower_la_SOURCES += module/pypower/bus.cpp module/pypower/bus.h
module_pypower_pypower_la_SOURCES += module/pypower/gen.cpp module/pypower/gen.h
module_pypower_pypower_la_SOURCES += module/pypower/gencost.cpp module/pypower/gencost.h
module_pypower_pypower_la_SOURCES += module/pypower/geodata.cpp module/pypower/geodata.h
module_pypower_pypower_la_SOURCES += module/pypower/load.cpp module/pypower/load.h
module_pypower_pypower_la_SOURCES += module/pypower/powerline.cpp module/pypower/powerline.h
module_pypower_pypower_la_SOURCES += module/pypower/powerplant.cpp module/pypower/powerplant.h
module_pypower_pypower_la_SOURCES += module/pypower/relay.cpp module/pypower/relay.h
module_pypower_pypower_la_SOURCES += module/pypower/scada.cpp module/pypower/scada.h
module_pypower_pypower_la_SOURCES += module/pypower/shunt.cpp module/pypower/shunt.h
module_pypower_pypower_la_SOURCES += module/pypower/transformer.cpp module/pypower/transformer.h
module_pypower_pypower_la_SOURCES += module/pypower/weather.cpp module/pypower/weather.h

dist_pkgdata_DATA += module/pypower/pypower_solver.py
