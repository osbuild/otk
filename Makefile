.PHONY: lint
lint:
	@find . -name '*.yaml' | xargs yamllint

.PHONY: type
type:
	@mypy src/ test/

.PHONY: format
format:
	@ruff format src/ test/

.PHONY: test
test:
	@pytest
