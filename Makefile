targets := test docinc html spdx

all: $(targets)
.PHONY: all

test:
	py.test --cov=scorpy

docinc:
	./doc_examples/gen_all.py doc_examples doc_examples/output

html:
	$(MAKE) -C doc html

spdx:
	@echo "Files without SPDX identifier:"
	@rg --files-without-match -tpy SPDX-License-Identifier
