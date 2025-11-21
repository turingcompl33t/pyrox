# Perform quality assurance checks on the (Python) source
# code located in the src/ directory.
# Execution of the commands in this file requires installation
# of several Python packages from the requirements.txt file.

all: sort format lint typecheck

check: sort-check format-check lint-check typecheck-check

sort:
	isort src

sort-check:
	isort -c src

format:
	black src

format-check:
	black --check src

lint:
	flake8 src

lint-check: lint

typecheck:
	mypy src

typecheck-check: typecheck

test:
	pytest src

testall:
	pytest src --runslow
