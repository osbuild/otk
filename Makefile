.PHONY: lint
lint:
	@find . -name '*.yaml' | xargs yamllint
	@ruff check

.PHONY: type
type:
	@mypy src/ test/

.PHONY: format
format:
	@ruff format src/ test/

.PHONY: test
test:
	@pytest
	pre-commit run --all-files

.PHONY: git-diff-check
git-diff-check:
	@git diff --exit-code
	@git diff --cached --exit-code

## Package building
COMMIT = $(shell (cd "$(SRCDIR)" && git rev-parse HEAD))
RPM_SPECFILE=rpmbuild/SPECS/otk-$(COMMIT).spec
RPM_TARBALL=rpmbuild/SOURCES/otk-$(COMMIT).tar.gz

$(RPM_SPECFILE):
	mkdir -p $(CURDIR)/rpmbuild/SPECS
	(echo "%global commit $(COMMIT)"; git show HEAD:otk.spec) > $(RPM_SPECFILE)

$(RPM_TARBALL):
	mkdir -p $(CURDIR)/rpmbuild/SOURCES
	git archive --prefix=otk-$(COMMIT)/ --format=tar.gz HEAD > $(RPM_TARBALL)

.PHONY: srpm
srpm: git-diff-check $(RPM_SPECFILE) $(RPM_TARBALL)
	rpmbuild -bs \
		--define "_topdir $(CURDIR)/rpmbuild" \
		$(RPM_SPECFILE)

.PHONY: rpm
rpm: git-diff-check $(RPM_SPECFILE) $(RPM_TARBALL)
	rpmbuild -bb \
		--define "_topdir $(CURDIR)/rpmbuild" \
		$(RPM_SPECFILE)
