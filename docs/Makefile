# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS      =
SPHINXBUILD     = sphinx-build
PAPER           =
BUILDROOT       = build
DEPLOYROOT      = ~/deploy
DEPLOYDIRECTORY = $(DEPLOYROOT)/docs/minimongo

RSYNCDELETEOPT  = --delete
SSHCONFIG       = docs
REMOTEROOT      = ~/deploy
REMOTEDIRECTORY = $(REMOTEROOT)/docs/minimongo

# User-friendly check for sphinx-build
ifeq ($(shell which $(SPHINXBUILD) >/dev/null 2>&1; echo $$?), 1)
    $(error "The '$(SPHINXBUILD)' command was not found. Make sure you have Sphinx installed, then set the SPHINXBUILD environment variable to point to the full path of the '$(SPHINXBUILD)' executable. Alternatively you can add the directory with the executable to your PATH. If you don't have Sphinx installed, grab it from http://sphinx-doc.org/")
endif

# Internal variables.
ALLSPHINXOPTS   = -d $(BUILDROOT)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source

.PHONY: help clean deploy html coverage

default: html

help:
	@echo "Usage: 'make <target>' where <target> is one of"
	@echo "  deploy     to deploy HTML files remotely"
	@echo "  html       to make standalone HTML files"
	@echo "  coverage   to run coverage check of the documentation (if enabled)"

clean:
	rm -rf $(BUILDROOT)/*

deploy: html

	@mkdir -p $(DEPLOYDIRECTORY)
	@cp -r $(BUILDROOT)/html/* $(DEPLOYDIRECTORY)
	@ssh $(SSHCONFIG) 'mkdir -p $(REMOTEDIRECTORY)'
	rsync -avze 'ssh' --exclude '.git*' $(DEPLOYDIRECTORY)/ $(SSHCONFIG):$(REMOTEDIRECTORY)
	@echo
	@echo "Deploy finished. The HTML pages have been copied and deployed remotely."
	@echo "  << $(DEPLOYDIRECTORY)"
	@echo "  >> $(SSHCONFIG):$(REMOTEDIRECTORY)"


html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDROOT)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDROOT)/html."

coverage:
	$(SPHINXBUILD) -b coverage $(ALLSPHINXOPTS) $(BUILDROOT)/coverage
	@echo "Testing of coverage in the sources finished, look at the " \
	      "results in $(BUILDROOT)/coverage/python.txt."
