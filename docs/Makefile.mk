
DOCS = 
DOCS += docs/Utilities/Framework.md
DOCS += docs/Utilities/Network.md
DOCS += docs/Utilities/Model.md
DOCS += docs/Utilities/Mapping.md
DOCS += docs/Utilities/Unitcalc.md

%.md: FORCE
	echo "Updating $@"
	$(DESTDIR)$(bindir)/gridlabd python docs/makemd.py $(basename $(notdir $(shell echo "$@" | tr 'A-Z' 'a-z'))) $(dir $@)

docs/Utilities: $(DOCS)

FORCE:
