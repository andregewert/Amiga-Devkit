# charcheck.mk - refuses UTF-8 in files that must be ISO-8859-1 (amiga-devkit)
#
# Amiga sources, catalogs and texts are ISO-8859-1. The project sets LATIN1
# to the list of these files before including this, e.g.
#
#   LATIN1 := $(wildcard src/*.c src/*.h package/* LICENSE Makefile)
#   include amiga-devkit/make/charcheck.mk
#
# and makes "all" depend on charcheck. The test finds UTF-8 sequences: a
# lead byte 0xC2-0xF4 followed by a continuation byte. ISO-8859-1 text
# rarely has such a pair (e.g. "Ã©"), so the check gives no false alarms
# on German texts.

charcheck:
	@if LC_ALL=C grep -lP '[\xC2-\xF4][\x80-\xBF]' $(LATIN1); then \
		echo "*** The files above contain UTF-8, please convert them to ISO-8859-1"; exit 1; fi

.PHONY: charcheck
