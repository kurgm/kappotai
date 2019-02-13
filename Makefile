READSVG=scripts/readsvg.py
WRITESVG=scripts/writesvg.py
MKOTF=scripts/mkotf.py
INKSCAPE=inkscape

YAMLS:=$(wildcard data/*.yaml)
UNIONSVGS:=$(YAMLS:data/%.yaml=build/union/%.svg)

TARGET=build/kappotai.otf

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

build/kappotai.otf: $(UNIONSVGS)
	$(MKOTF) -o $@ build/union kappotai.yaml

build/kappotai.otf: $(MKOTF) kappotai.yaml

clean:
	-$(RM) -r build edit

.PHONY: all clean
