
docs: docs/Tools

DOCS_UTILITIES = $(DESTDIR)$(bindir)/gridlabd docs/makemd.py

include $(top_srcdir)/docs/Tools/Makefile.mk

docs/Tools: $(DOCS_UTILITIES)
	@test "$(MAKEMD)" != "no" && echo "Updating $@..." || true

%.md: .FORCE
	@test "$(MAKEMD)" != "no" && $(DESTDIR)$(bindir)/gridlabd python docs/makemd.py $(basename $(notdir $(shell echo "$@" | tr 'A-Z' 'a-z'))) $(dir $@) || true

.FORCE:
