# docs.mk - HTML documentation with Doxygen (amiga-devkit)
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

DOXYGEN ?= doxygen
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
