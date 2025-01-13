
docs: docs/Utilities

DOCS_UTILITIES = 
DOCS_UTILITIES += docs/Utilities/Framework.md
DOCS_UTILITIES += docs/Utilities/Network.md
DOCS_UTILITIES += docs/Utilities/Edit.md
DOCS_UTILITIES += docs/Utilities/Mapping.md
DOCS_UTILITIES += docs/Utilities/Unitcalc.md

docs/Utilities: $(DOCS_UTILITIES)
	echo "Updating $@..."

%.md: FORCE
	$(DESTDIR)$(bindir)/gridlabd python docs/makemd.py $(basename $(notdir $(shell echo "$@" | tr 'A-Z' 'a-z'))) $(dir $@)

FORCE:
