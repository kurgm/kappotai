READSVG=scripts/readsvg.py
WRITESVG=scripts/writesvg.py
MKOTF=scripts/mkotf.py

INKSCAPE=inkscape
MAKEOTF=makeotf
TX=tx
MERGEFONTS=mergefonts

YAMLS:=$(wildcard data/*.yaml)
UNIONSVGS:=$(YAMLS:data/%.yaml=build/union/%.svg)
INVERTSVGS:=$(YAMLS:data/%.yaml=build/invert/%.svg)

COMMONSVGS:=$(wildcard glyph/common/*.svg)

KAPPOTAIW_SVGS=$(UNIONSVGS) $(COMMONSVGS)
KAPPOTAIB_SVGS=$(INVERTSVGS) $(COMMONSVGS)

TARGET=build/kappotaiw.otf build/kappotaib.otf

all: $(TARGET)

edit build:
	mkdir -p $@

ifdef EDITED_SVG

data/%.yaml: edit/%.svg
	$(READSVG) -o $@ $<

.PRECIOUS: data/%.yaml

else

edit/%.svg: data/%.yaml $(WRITESVG) scripts/edit.css | edit
	$(WRITESVG) -o $@ $<

build/deps.mk: $(YAMLS) scripts/mkdeps.py | build
	scripts/mkdeps.py -o $@

include build/deps.mk

endif

build/expand:
	mkdir -p $@

build/expand/%.svg: data/%.yaml $(WRITESVG) scripts/edit.css | build/expand
	$(WRITESVG) -o $@ --expand $<

build/union:
	mkdir -p $@

build/union/%.svg: build/expand/%.svg | build/union
	cp $< $@
	$(INKSCAPE) --with-gui \
		--verb EditSelectAll \
		--verb StrokeToPath \
		--verb SelectionUnion \
		--verb FileSave \
		--verb FileQuit \
		"$(abspath $@)"

.DELETE_ON_ERROR: build/union/%.svg

build/invert:
	mkdir -p $@

build/invert/%.svg: build/union/%.svg scripts/unhide_bbx.py | build/invert
	scripts/unhide_bbx.py $< > $@
	$(INKSCAPE) --with-gui \
		--verb EditSelectAll \
		--verb SelectionDiff \
		--verb FileSave \
		--verb FileQuit \
		"$(abspath $@)"

.DELETE_ON_ERROR: build/invert/%.svg

build/kappotaiw build/kappotaib:
	mkdir -p $@

build/kappotaiw/namekeyed.otf: $(MKOTF) $(KAPPOTAIW_SVGS) glyph/common.txt kappotaiw.yaml | build/kappotaiw
	$(MKOTF) -o $@ -m kappotaiw.yaml @glyph/common.txt build/union

build/kappotaib/namekeyed.otf: $(MKOTF) $(KAPPOTAIB_SVGS) glyph/common.txt kappotaib.yaml | build/kappotaib
	$(MKOTF) -o $@ -m kappotaib.yaml @glyph/common.txt build/invert

build/%/features_vmtx: scripts/mkvmtxfeat.py fontmeta/kappotai.map build/%/namekeyed.otf
	scripts/mkvmtxfeat.py -o $@ $(word 2,$^) $(word 3,$^)

build/%/font.cff: fontmeta/%_cidfontinfo fontmeta/kappotai.map build/%/namekeyed.otf
	$(MERGEFONTS) -cid $(word 1,$^) $@ $(word 2,$^) $(word 3,$^)

build/%/font.ps: build/%/font.cff
	$(TX) -t1 $< $@

ifdef DEV
MAKEOTFOPT?=
else
MAKEOTFOPT?=-r
endif

build/%.otf: build/%/font.ps fontmeta/%_features fontmeta/%_fontMenuNameDB fontmeta/uvs_sequences.txt fontmeta/common_features build/%/features_vmtx
	$(MAKEOTF) $(MAKEOTFOPT) -f $(word 1,$^) -ff $(word 2,$^) -mf $(word 3,$^) -ci $(word 4,$^) -o $@

.DELETE_ON_ERROR: build/%/font.cff build/%/font.ps build/%.otf

ifndef DEV

RELEASENAME=kappotai0500

RELEASEFILES=README.txt
RELEASEFONTS=kappotaiw.otf kappotaib.otf

RELEASEFILES:=$(RELEASEFILES:%=build/$(RELEASENAME)/%)
RELEASEFONTS:=$(RELEASEFONTS:%=build/$(RELEASENAME)/%)

build/$(RELEASENAME):
	mkdir -p $@

$(RELEASEFONTS): build/$(RELEASENAME)/%.otf: build/%.otf | build/$(RELEASENAME)
	cp -p $< $@

$(RELEASEFILES): build/$(RELEASENAME)/%: release/% | build/$(RELEASENAME)
	cp -p $< $@

build/$(RELEASENAME).zip: $(RELEASEFILES) $(RELEASEFONTS)
	cd $(@D); \
	$(RM) $(@F) || true; \
	zip -r $(@F) $(RELEASENAME)

release: build/$(RELEASENAME).zip

endif

clean:
	-$(RM) -r build edit

.PHONY: all clean
