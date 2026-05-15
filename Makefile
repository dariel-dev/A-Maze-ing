VENV     := maze_env
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
WHEEL    := mazegen-1.0.0-py3-none-any.whl

.PHONY: install run debug clean lint lint-strict build help start

help:
	@echo "Targets: install run debug clean lint lint-strict build start"

start:
	python3 a_maze_ing.py config.txt

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install ./$(WHEEL)

install: $(VENV)/bin/activate

run: install
	$(PYTHON) a_maze_ing.py config.txt

debug: install
	$(PYTHON) -m pdb a_maze_ing.py config.txt

lint: install
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --warn-return-any --warn-unused-ignores \
	    --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: install
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict

build: install
	$(PYTHON) -m build --wheel --outdir .

clean:
	rm -rf $(VENV) build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
