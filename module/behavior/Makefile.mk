# module/behavior/Makefile.mk
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

pkglib_LTLIBRARIES += module/behavior/behavior.la

module_behavior_behavior_la_CPPFLAGS =
module_behavior_behavior_la_CPPFLAGS += $(AM_CPPFLAGS)

module_behavior_behavior_la_LDFLAGS =
module_behavior_behavior_la_LDFLAGS += $(AM_LDFLAGS)

module_behavior_behavior_la_LIBADD = 

module_behavior_behavior_la_SOURCES =
module_behavior_behavior_la_SOURCES += module/behavior/behavior.cpp module/behavior/behavior.h
module_behavior_behavior_la_SOURCES += module/behavior/system.cpp module/behavior/system.h

module_behavior_behavior_la_SOURCES += module/behavior/random.cpp module/behavior/random.h
