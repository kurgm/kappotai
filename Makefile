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

TARGET=build/kappotaiw.otf build/kappotaib.otf

all: $(TARGET)

edit:
	mkdir -p $@

ifdef EDITED_SVG

data/%.yaml: edit/%.svg
	$(READSVG) -o $@ $<

else

edit/%.svg: data/%.yaml $(WRITESVG) scripts/edit.css | edit
	$(WRITESVG) -o $@ $<

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

build/kappotaiw/namekeyed.otf: $(MKOTF) $(COMMONSVGS) glyph/common.txt $(UNIONSVGS) kappotaiw.yaml | build/kappotaiw
	$(MKOTF) -o $@ -m kappotaiw.yaml @glyph/common.txt build/union

build/kappotaib/namekeyed.otf: $(MKOTF) $(COMMONSVGS) glyph/common.txt $(INVERTSVGS) kappotaib.yaml | build/kappotaib
	$(MKOTF) -o $@ -m kappotaib.yaml @glyph/common.txt build/invert

build/%/font.cff: fontmeta/%_cidfontinfo fontmeta/kappotai.map build/%/namekeyed.otf
	$(MERGEFONTS) -cid $(word 1,$^) $@ $(word 2,$^) $(word 3,$^)

build/%/font.ps: build/%/font.cff
	$(TX) -t1 $< $@

build/%.otf: build/%/font.ps fontmeta/%_features fontmeta/%_fontMenuNameDB fontmeta/common_features
	$(MAKEOTF) -f $(word 1,$^) -ff $(word 2,$^) -mf $(word 3,$^) -o $@

.DELETE_ON_ERROR: build/%/font.cff build/%/font.ps build/%.otf

clean:
	-$(RM) -r build edit

.PHONY: all clean
