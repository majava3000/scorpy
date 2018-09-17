targets := test docinc html

all: $(targets)
.PHONY: all

test:
	py.test --cov=scorpy

docinc:
	./doc_examples/gen_all.py doc_examples doc_examples/output

html:
	$(MAKE) -C doc html
