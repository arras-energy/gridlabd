
DOCS = 
DOCS += docs/Utilities/Glutils.md
DOCS += docs/Utilities/Glunits.md

%.md: FORCE
	echo "Updating $@"
	gridlabd python docs/makemd.py $(basename $(notdir $(shell echo "$@" | tr 'A-Z' 'a-z'))) $(dir $@)

docs/Utilities: $(DOCS)

FORCE:
