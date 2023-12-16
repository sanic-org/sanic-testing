pretty:
	black --line-length 79 sanic_testing tests
	isort --line-length 79 sanic_testing tests
install:
	python -m venv venv
	venv/bin/pip install --editable .[dev]
test:
	venv/bin/pytest tests
