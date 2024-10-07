# needed for venv
.ONESHELL:
SHELL := /bin/bash
.SHELLFLAGS := -ec -o pipefail

.PHONY: help
help:
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk 'match($$0, /^([a-zA-Z_\/-]+):.*?## (.*)$$/, m) {printf "  \033[36m%-30s\033[0m %s\n", m[1], m[2]}' $(MAKEFILE_LIST) | sort

# Keep this in sync with e.g. https://github.com/containers/podman/blob/2981262215f563461d449b9841741339f4d9a894/Makefile#L51
CONTAINERS_STORAGE_THIN_TAGS=containers_image_openpgp exclude_graphdriver_btrfs exclude_graphdriver_devicemapper
IMAGES_REF ?= github.com/osbuild/images

SRC_DIR?=$(CURDIR)
EXTERNAL_DIR?=$(SRC_DIR)/external
VENV_DIR?=$(SRC_DIR)/venv

EXTERNAL_GO_EXECUTABLES:= osbuild-gen-partition-table \
                          osbuild-make-fstab-stage \
                          osbuild-make-grub2-inst-stage \
                          osbuild-resolve-containers \
                          osbuild-resolve-ostree-commit \
                          osbuild-make-partition-mounts-devices \
                          osbuild-make-partition-stages

EXTERNAL_GO_EXECUTABLES_FULLPATH:=$(addprefix $(EXTERNAL_DIR)/, $(EXTERNAL_GO_EXECUTABLES))

check-pre-commit: # internal rule to check if pre-commit is installed
	@which pre-commit >/dev/null 2>&1 || { \
          echo >&2 -e "Please install https://pre-commit.com !\n"; \
	  echo >&2 "Either with 'pip install pre-commit'"; \
	  echo >&2 "or your package manager e.g. 'sudo dnf install pre-commit'"; \
	  exit 1; \
	}


SRC_CONTAINER_FILES=$(shell find src 2>/dev/null|| echo "src") \
                    Makefile \
                    pyproject.toml

container_built.info: Containerfile $(SRC_CONTAINER_FILES) # internal rule to avoid rebuilding if not necessary
	podman build --build-arg CONTAINERS_STORAGE_THIN_TAGS="$(CONTAINERS_STORAGE_THIN_TAGS)" \
	             --build-arg IMAGES_REF="$(IMAGES_REF)" \
	             --tag otk \
	             --pull=newer . &&
	echo "Container last built on" > $@ &&
	date >> $@

.PHONY: container
container: container_built.info ## rebuild the upstream container "ghcr.io/osbuild/otk" locally

CONTAINER_TEST_FILE?=example/centos/centos-9-x86_64-tar.yaml

.PHONY: container-test
container-test: container ## run an example command in the container to test it
	podman run --rm -ti -v .:/app otk:latest compile /app/$(CONTAINER_TEST_FILE)

.PHONY: lint
lint: check-pre-commit ## run all linters against the project
	pre-commit run --all-files

.PHONY: type
type: check-pre-commit ## run type checks
	pre-commit run --all-files mypy

.PHONY: format
format: ## format all python source files
	@find src test -name '*.py' | xargs autopep8 --in-place

.PHONY: test
test: external | $(VENV_DIR) ## run all tests
	. $(VENV_DIR)/bin/activate
	@pytest

.PHONY: push-check
push-check: test lint type ## run tests, linters and type checks to avoid problems in a pull request

.PHONY: git-diff-check
git-diff-check: # internal rule to check for git changes
	@git diff --exit-code
	@git diff --cached --exit-code

## Package building
SRCDIR ?= $(abspath .)
COMMIT = $(shell (cd "$(SRCDIR)" && git rev-parse HEAD 2>/dev/null || echo "INVALID" ))
RPM_BUILD_DIR?=rpmbuild
RPM_SPECFILE=$(RPM_BUILD_DIR)/SPECS/otk-$(COMMIT).spec
RPM_TARBALL=$(RPM_BUILD_DIR)/SOURCES/otk-$(COMMIT).tar.gz

$(RPM_SPECFILE):
	mkdir -p $(CURDIR)/rpmbuild/SPECS
	(echo "%global commit $(COMMIT)"; git show HEAD:otk.spec 2>/dev/null || echo "INVALID SETUP" ) > $(RPM_SPECFILE)

$(RPM_TARBALL): # internal rule to creat the source tar ball
	mkdir -p $(CURDIR)/$(RPM_BUILD_DIR)/SOURCES
	git archive --prefix=otk-$(COMMIT)/ --format=tar.gz HEAD > $(RPM_TARBALL)

.PHONY: srpm
srpm: git-diff-check $(RPM_SPECFILE) $(RPM_TARBALL) ## create the source RPM
	rpmbuild -bs \
		--define "_topdir $(CURDIR)/$(RPM_BUILD_DIR)" \
		$(RPM_SPECFILE)

.PHONY: rpm
rpm: git-diff-check $(RPM_SPECFILE) $(RPM_TARBALL) rpm-prerequisites | $(VENV_DIR) ## create the RPM
	. $(VENV_DIR)/bin/activate
	rpmbuild -bb \
		--define "_topdir $(CURDIR)/$(RPM_BUILD_DIR)" \
		$(RPM_SPECFILE)

rpm-prerequisites: # internal rule to install packages needed to build the RPM
	sudo dnf install -y python3-wheel

$(EXTERNAL_DIR):
	mkdir -p $@

$(EXTERNAL_GO_EXECUTABLES_FULLPATH): | $(EXTERNAL_DIR)
	GOBIN=$(dir $@) go install -tags "$(CONTAINERS_STORAGE_THIN_TAGS)" "$(IMAGES_REF)"/cmd/otk/$(notdir $@)@main ;

# Note that "external" will most likely in the future build from internal
# sources instead of pulling of the network
.PHONY: external
external: $(EXTERNAL_GO_EXECUTABLES_FULLPATH) pyexternals

pyexternals: $(VENV_DIR)
	ln -sf $(VENV_DIR)/bin/osbuild-* $(EXTERNAL_DIR)/

clean: ## clean all build artifacts
	rm -rf $(VENV_DIR)
	rm -rf $(EXTERNAL_DIR)
	rm -rf $(RPM_BUILD_DIR)

$(VENV_DIR): pyproject.toml | $(EXTERNAL_DIR)
	python3 -m venv $@
	. $@/bin/activate
	pip install -e ".[dev]"
	touch $@
