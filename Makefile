.PHONY: shell test-create-db test todo qa pylint-report pylint pep8 clean


PROJ=tracked_model
VENV=3.4.2
TEST_DIR=tests/
PYTEST_OPTS=--cov-report term-missing --cov-config $(COV_CFG) --cov
COV_CFG=$(TEST_DIR)cov.ini
PYLINT_OPTS=--rcfile pylint.rc --load-plugins pylint_django


clean:
	@find ./ -name __pycache__ | xargs rm -fr; find ./ -name '*pyc' -delete; find ./ -name '*.swp' -delete; rm -fr dist *.egg-info


pep8:
	@pep8 --exclude=migrations $(PROJ) $(TEST_DIR)


pylint:
	@pylint -r n  --disable=fixme $(PYLINT_OPTS) $(PROJ) $(TEST_DIR)


pylint-report:
	@pylint --disable=fixme $(PYLINT_OPTS) $(PROJ) $(TEST_DIR)


qa:
	@((pep8 --exclude=migrations $(PROJ) $(TEST_DIR) && pylint -r n $(PYLINT_OPTS) $(PROJ) $(TEST_DIR)) && echo 'All good') || echo 'Nope'


todo:
	@pylint -r n --disable=all --enable=fixme $(PROJ)


test:
	@py.test $(PYTEST_OPTS) $(PROJ) $(TEST_DIR)


test-create-db:
	@py.test --create-db $(PYTEST_OPTS) $(PROJ) $(TEST_DIR)


shell:
	@. venv/$(VENV)/bin/activate; ipython


sdist:
	python setup.py sdist
