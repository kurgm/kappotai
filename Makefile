READSVG=scripts/readsvg.py
WRITESVG=scripts/writesvg.py
MKOTF=scripts/mkotf.py
INKSCAPE=inkscape

YAMLS:=$(wildcard data/*.yaml)
UNIONSVGS:=$(YAMLS:data/%.yaml=build/union/%.svg)
INVERTSVGS:=$(YAMLS:data/%.yaml=build/invert/%.svg)

TARGET=build/kappotaiw.otf build/kappotaib.otf

all: $(TARGET)

edit:
	mkdir -p $@

ifdef EDITED_SVG

data/%.yaml: edit/%.svg
	$(READSVG) -o $@ $<

else

edit/%.svg: data/%.yaml | edit
	$(WRITESVG) -o $@ $<

endif

build:
	mkdir -p $@

build/expand:
	mkdir -p $@

build/expand/%.svg: data/%.yaml | build/expand
	$(WRITESVG) -o $@ --expand $<

build/expand/%.svg: $(WRITESVG)

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

build/invert/%.svg: build/union/%.svg | build/invert
	scripts/unhide_bbx.py $< > $@
	$(INKSCAPE) --with-gui \
		--verb EditSelectAll \
		--verb SelectionDiff \
		--verb FileSave \
		--verb FileQuit \
		"$(abspath $@)"

build/invert/%.svg: scripts/unhide_bbx.py

.DELETE_ON_ERROR: build/invert/%.svg

build/kappotaiw.otf: $(MKOTF) $(UNIONSVGS) kappotaiw.yaml
	$(MKOTF) -o $@ build/union kappotaiw.yaml

build/kappotaib.otf: $(MKOTF) $(INVERTSVGS) kappotaib.yaml
	$(MKOTF) -o $@ build/invert kappotaib.yaml

clean:
	-$(RM) -r build edit

.PHONY: all clean
