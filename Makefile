PYTHON ?= python

.PHONY: lint format-check typecheck test check schema-check precommit compose-check
lint:
	$(PYTHON) -m ruff check .
format-check:
	$(PYTHON) -m ruff format --check .
typecheck:
	$(PYTHON) -m mypy finagent eval
test:
	$(PYTHON) -m pytest
schema-check:
	$(PYTHON) -m finagent.schema_catalog --check
precommit:
	$(PYTHON) -m pre_commit run --all-files --hook-stage manual
compose-check:
	docker compose config --quiet
check: lint format-check typecheck test schema-check

