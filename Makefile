
check-pre-commit:
	@which pre-commit >/dev/null 2>&1 || { \
          echo >&2 -e "Please install https://pre-commit.com !\n"; \
	  echo >&2 "Either with 'pip install pre-commit'"; \
	  echo >&2 "or your package manager e.g. 'sudo dnf install pre-commit'"; \
	  exit 1; \
	}

.PHONY: lint
lint: check-pre-commit
	pre-commit run --all-files

.PHONY: type
type: check-pre-commit
	pre-commit run --all-files mypy

.PHONY: format
format:
	@find src test -name '*.py' | xargs autopep8 --in-place

.PHONY: test
test: external
	@pytest

.PHONY: push-check
push-check: test lint type

.PHONY: git-diff-check
git-diff-check:
	@git diff --exit-code
	@git diff --cached --exit-code

## Package building
SRCDIR ?= $(abspath .)
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

# Note that "external" will most likely in the future build from internal
# sources instead of pulling of the network
.PHONY: external
# # Keep this in sync with e.g. https://github.com/containers/podman/blob/2981262215f563461d449b9841741339f4d9a894/Makefile#L51
CONTAINERS_STORAGE_THIN_TAGS=containers_image_openpgp exclude_graphdriver_btrfs exclude_graphdriver_devicemapper
IMAGES_REF ?= github.com/osbuild/images
external:
	mkdir -p "$(SRCDIR)/external"
	set -e ; \
	for otk_cmd in gen-partition-table \
			make-fstab-stage \
			make-partition-mounts-devices \
			make-partition-stages; do \
		GOBIN="$(SRCDIR)/external" go install -tags "$(CONTAINERS_STORAGE_THIN_TAGS)" "$(IMAGES_REF)"/cmd/otk-$${otk_cmd}@main ; \
	done
