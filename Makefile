READSVG=scripts/readsvg.py
WRITESVG=scripts/writesvg.py

all:
	echo "Not configured yet"
	exit 1

edit:
	mkdir -p edit

ifdef EDITED_SVG

data/%.yaml: edit/%.svg
	$(READSVG) -o $@ $<

else

edit/%.svg: data/%.yaml | edit
	$(WRITESVG) -o $@ $<

endif

clean:
	@rm -r build
	@rm -r edit

.PHONY: all clean
