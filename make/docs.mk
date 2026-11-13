# docs.mk - HTML and AmigaGuide documentation with Doxygen (amiga-devkit)
#
# The project defines one or more documentation targets with DOXYGEN_DOCS:
#
#   include amiga-devkit/make/docs.mk
#   $(eval $(call DOXYGEN_DOCS,docs,MyProgram,1.0,src include,build/docs))
#   $(eval $(call DOXYGEN_DOCS,docs-my.gadget,my.gadget,1.0,include/gadgets/my.h,build/docs/my.gadget))
#
# Arguments: make target, project name, version, input files or
# directories (space separated), output directory. The target writes HTML
# to <output>/html and fails if Doxygen warned (missing or wrong comments);
# the warnings are in <output>/warnings.txt. The configuration is
# doxygen/Doxyfile.base; the rules for the comments are in
# docs/Dokumentation.md. Doxygen is only needed for these targets, never
# for building the program. DOXYGEN names the program (default: doxygen).
#
# DOXYGEN_GUIDE makes an AmigaGuide reference from the same comments, for
# Amiga users (Amiga browsers cannot show Doxygen's HTML):
#
#   $(eval $(call DOXYGEN_GUIDE,guide,my.library,1.0 (01.10.2026),include/libraries/my.h include/clib/my_protos.h,build/my.library.guide))
#
# Arguments as above, but the last one is the guide file. Doxygen writes
# XML next to it (<guide>.xml/), tools/doxy2guide.py turns that into one
# guide in ISO-8859-1 (only the compounds listed in index.xml are read, so
# files left over from an earlier run do no harm). The version goes into
# the guide's $VER as given. PYTHON names the interpreter (default: python3).
# The HTML is made too (<guide>.xml/html, unused): without it Doxygen 1.9.8
# warns that every documented parameter and return value is undocumented.

DOXYGEN ?= doxygen
PYTHON ?= python3
DOCS_DEVKIT := $(patsubst %/make/docs.mk,%,$(lastword $(MAKEFILE_LIST)))

# $(1) target, $(2) name, $(3) version, $(4) input, $(5) output directory
define DOXYGEN_DOCS
.PHONY: $(1)
$(1):
	@mkdir -p $(5)
	@( cat $(DOCS_DEVKIT)/doxygen/Doxyfile.base; \
	   echo 'PROJECT_NAME = "$(2)"'; \
	   echo 'PROJECT_NUMBER = "$(3)"'; \
	   echo 'INPUT = $(4)'; \
	   echo 'STRIP_FROM_PATH = $(CURDIR)'; \
	   echo 'OUTPUT_DIRECTORY = $(5)'; \
	   echo 'WARN_LOGFILE = $(5)/warnings.txt' ) | $(DOXYGEN) -
	@if [ -s $(5)/warnings.txt ]; then cat $(5)/warnings.txt; \
		echo "*** $$$$(wc -l < $(5)/warnings.txt) documentation warnings, see above"; exit 1; fi
	@echo "Documentation: $(5)/html/index.html"
endef

# $(1) target, $(2) name, $(3) version, $(4) input, $(5) guide file
define DOXYGEN_GUIDE
.PHONY: $(1)
$(1):
	@mkdir -p $(5).xml
	@( cat $(DOCS_DEVKIT)/doxygen/Doxyfile.base; \
	   echo 'PROJECT_NAME = "$(2)"'; \
	   echo 'INPUT = $(4)'; \
	   echo 'STRIP_FROM_PATH = $(CURDIR)'; \
	   echo 'OUTPUT_DIRECTORY = $(5).xml'; \
	   echo 'GENERATE_XML = YES'; \
	   echo 'XML_PROGRAMLISTING = NO'; \
	   echo 'WARN_LOGFILE = $(5).xml/warnings.txt' ) | $(DOXYGEN) - >/dev/null
	@if [ -s $(5).xml/warnings.txt ]; then cat $(5).xml/warnings.txt; \
		echo "*** $$$$(wc -l < $(5).xml/warnings.txt) documentation warnings, see above"; exit 1; fi
	@$(PYTHON) $(DOCS_DEVKIT)/tools/doxy2guide.py $(5).xml/xml $(5) --name '$(2)' --version '$(3)'
	@echo "AmigaGuide: $(5)"
endef
