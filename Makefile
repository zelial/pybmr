test:
	tox

requirements.txt: requirements.in
	pip-compile -U --output-file requirements.txt requirements.in;

test-requirements.txt: test-requirements.in
	pip-compile -U --output-file test-requirements.txt test-requirements.in;

.PHONY: test
