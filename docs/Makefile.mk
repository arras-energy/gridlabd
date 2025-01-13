
docs: docs/Tools

DOCS_UTILITIES = 

include $(top_srcdir)/docs/Tools/Makefile.mk

docs/Tools: $(DOCS_UTILITIES)
	echo "Updating $@..."

%.md: FORCE
	$(DESTDIR)$(bindir)/gridlabd python docs/makemd.py $(basename $(notdir $(shell echo "$@" | tr 'A-Z' 'a-z'))) $(dir $@)

FORCE:
