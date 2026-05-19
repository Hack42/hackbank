PYTHON ?= python3

test:
	@. .venv/bin/activate && ${env} ${PYTHON} -m pytest  -vvv --cov=. --cov-report term-missing
venv: .venv/make_venv_complete ## Create virtual environment
.venv/make_venv_complete:
	${PYTHON} -m venv .venv
	. .venv/bin/activate && ${env} pip install -U pip
	. .venv/bin/activate && ${env} pip install -U pip-tools
	. .venv/bin/activate && ${env} python3 -m piptools compile requirements.in
	. .venv/bin/activate && ${env} python3 -m piptools compile requirements-dev.in
	. .venv/bin/activate && ${env} pip install -Ur requirements.txt
	. .venv/bin/activate && ${env} pip install -Ur requirements-dev.txt
	touch .venv/make_venv_complete

pip-compile: ## synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate && ${env} ${PYTHON} -m piptools compile requirements.in
	. .venv/bin/activate && ${env} ${PYTHON} -m piptools compile requirements-dev.in

pip-sync: ## synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate && ${env} ${PYTHON} -m piptools sync requirements.txt

pip-sync-dev: ## synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate && ${env} pip install -U pip-tools
	. .venv/bin/activate && ${env} ${PYTHON} -m piptools sync requirements.txt requirements-dev.txt

lint: venv  ## Do basic linting
	@. .venv/bin/activate && ${env} ${PYTHON} -m pylint --persistent=no kassa.py plugins
	@. .venv/bin/activate && ${env} ${PYTHON} -m black --check kassa.py plugins tests

check-types: venv ## Check for type issues with mypy
	@. .venv/bin/activate && ${env} ${PYTHON} -m mypy --check .

fix:
	@. .venv/bin/activate && ${env} ${PYTHON} -m black kassa.py plugins tests
