
docs/Utilities: tools/glutils.py tools/glunits.py
	$(foreach tool,$<,gridlabd python docs/makemd.py $(basename $(notdir $(tool))) $@)

