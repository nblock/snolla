# Makefile
# This file is part of snolla. See README for more information.

.PHONY: clean coverage-html tests

COVERAGE_HTML="htmlcov"
COVERAGE=".coverage"

tests:
	@python -m unittest discover --start-directory tests

coverage-html:
	@coverage run -m unittest discover --start-directory tests
	@coverage html --omit="*/site-packages/*" --directory=$(COVERAGE_HTML)

clean:
	@rm -rf $(COVERAGE_HTML)
