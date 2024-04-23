.PHONY: lint
lint: pre-commit
	@find . -name '*.yaml' | xargs yamllint

.PHONY: type
type:
	@mypy src/ test/

.PHONY: format
format:
	@ruff format src/ test/

.PHONY: test
test: pre-commit
	@pytest

.PHONY: pre-commit
pre-commit:
	@pre-commit run --all-files
