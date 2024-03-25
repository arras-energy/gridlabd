# module/human/Makefile.mk
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

pkglib_LTLIBRARIES += module/human/human.la

module_human_human_la_CPPFLAGS =
module_human_human_la_CPPFLAGS += $(AM_CPPFLAGS)

module_human_human_la_LDFLAGS =
module_human_human_la_LDFLAGS += $(AM_LDFLAGS)

module_human_human_la_LIBADD = 

module_human_human_la_SOURCES =
module_human_human_la_SOURCES += module/human/human.cpp module/human/human.h

module_human_human_la_SOURCES += module/human/random.cpp module/human/random.h
