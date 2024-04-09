lint:
	@find . -name '*.yaml' | xargs yamllint

.PHONY: lint
