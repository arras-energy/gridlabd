# module/pypower/Makefile.mk
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

pkglib_LTLIBRARIES += module/pypower/pypower.la

module_assert_assert_la_CPPFLAGS =
module_assert_assert_la_CPPFLAGS += $(AM_CPPFLAGS)

module_assert_assert_la_LDFLAGS =
module_assert_assert_la_LDFLAGS += $(AM_LDFLAGS)

module_assert_assert_la_LIBADD = 

module_assert_assert_la_SOURCES =
module_assert_assert_la_SOURCES += module/assert/main.cpp module/assert/pypower.h
module_assert_assert_la_SOURCES += module/assert/bus.cpp module/assert/bus.h
module_assert_assert_la_SOURCES += module/assert/branch.cpp module/assert/branch.h
module_assert_assert_la_SOURCES += module/assert/gen.cpp module/assert/gen.h
module_assert_assert_la_SOURCES += module/assert/gencost.cpp module/assert/gencost.h
