EXCLUDE := tests/calc.fn tests/file.fn tests/e120.fn examples/test.bf
TESTS := $(filter-out $(EXCLUDE), $(wildcard tests/*))
EXAMPLES := $(filter-out $(EXCLUDE), $(wildcard examples/*))
.PHONY: all examples

all:
	@for file in $(TESTS); do echo $$file && python3 main.py $$file|| exit 1; done

examples:
	@for file in $(EXAMPLES); do \
	echo $$file; \
	if [ "$$file" = "examples/bf.fn" ]; then \
		python3 main.py $$file examples/test.bf && echo '' || exit 1; \
	else \
		python3 main.py $$file || exit 1; \
	fi; \
	done
