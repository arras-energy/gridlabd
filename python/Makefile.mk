PYTHONVERSION=$(shell python$(PYVER) $(top_srcdir)/python/setup.py --version)
PYPKG=$(PYENV)/lib/python$(PYVER)/site-packages/gldcore

$(top_srcdir)/python/dist/gldcore-$(PYTHONVERSION).tar.gz: $(top_srcdir)/source/build.h $(wildcard $(top_srcdir)/source/*.cpp) | $(PYENV)
	@echo "building gldcore-$(PYTHONVERSION)..."
	@rm -f $(PYPKG)-$(PYTHONVERSION)*.{whl,tar.gz}
	@$(ENVPYTHON) -m pip install build 
	@export SRCDIR=$(realpath $(top_srcdir)) ; export BLDDIR=$(shell pwd); $(ENVPYTHON) -m build $(top_srcdir)/python

$(PYPKG)-$(PYTHONVERSION).tar.gz: $(top_srcdir)/python/dist/gldcore-$(PYTHONVERSION).tar.gz
	@echo "copying $(top_srcdir)/python/dist to $(PYPKG)-$(PYTHONVERSION)..."
	@cp $(top_srcdir)/python/dist/gldcore-$(PYTHONVERSION)*.{tar.gz,whl} $(PYENV)/lib/python$(PYVER)/site-packages

python-install: $(PYPKG)-$(PYTHONVERSION).dist-info
	@mkdir -p $(datadir)/$(PACKAGE)/ 
	@cp $(PYPKG)-$(PYTHONVERSION)-*.whl $(datadir)/$(PACKAGE)/ 

$(PYPKG)-$(PYTHONVERSION).dist-info: $(PYPKG)-$(PYTHONVERSION).tar.gz
	@echo "installing gldcore-$(PYTHONVERSION)..."
	$(ENVPYTHON) -m pip install --ignore-installed $(PYPKG)-$(PYTHONVERSION)-*.whl
	touch $@

python-clean:
	@echo "removing $(top_srcdir)/python/dist..."
	@rm -rf $(top_srcdir)/python/dist

python-uninstall:
	@echo "removing $(PYPKG)..."
	@rm -rf $(PYPKG)*

BUILT_SOURCES += python-install

pkginclude_HEADERS += $(wildcard $(top_srcdir)/python/*.h)
