READSVG=scripts/readsvg.py
WRITESVG=scripts/writesvg.py
YAMLS:=$(wildcard data/*.yaml)
UNIONSVGS:=$(YAMLS:data/%.yaml=build/union/%.svg)
DISPLAY=:99
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

build/union:
	mkdir -p $@

build/union/%.svg: build/expand/%.svg | build/union build/temp_display
	cp $< $@
	DISPLAY=$(DISPLAY) inkscape --with-gui \
		--verb EditSelectAll \
		--verb StrokeToPath \
		--verb SelectionUnion \
		--verb FileSave \
		--verb FileQuit \
		"$(abspath $@)"

.DELETE_ON_ERROR: build/union/%.svg

build/temp_display: | build
	Xvfb $(DISPLAY) & echo "kill -15 $$!" > $@

.PRECIOUS: build/temp_display

kill_display:
	-bash build/temp_display && $(RM) build/temp_display

.PHONY: kill_display

build/kappotai.otf: $(UNIONSVGS)
	echo "Not configured yet"
	exit 1

clean:
	-$(RM) -r build edit

.PHONY: all clean
