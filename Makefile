all: gentoo-family.svg
clean:
	rm -f gentoo-family.svg gentoo-family.dot devs.ldif

%.svg: %.dot
	rm -f $@ $@.tmp
	dot -Tsvg $< > $@.tmp
	mv $@.tmp $@

gentoo-family.dot: devs.ldif
	rm -f $@.tmp $@
	./ldif2dot.py $< > $@.tmp
	mv $@.tmp $@

devs.ldif:
	rm -f $@.tmp $@
	ssh dev.gentoo.org "ldapsearch -x -Z uid gentooMentor gentooStatus -LLL" > $@.tmp
	mv $@.tmp $@

.PHONY: all clean
