SHELL := /bin/zsh

PYTHON ?= python3
NPM ?= npm
HA_SOURCE_CONFIG ?= /Volumes/config
LOCAL_HA_CONFIG ?= $(HA_SOURCE_CONFIG)
COMPONENT_NAME := bereginya_aura
COMPONENT_REPO_SRC := custom_components/$(COMPONENT_NAME)
COMPONENT_HA_SRC := $(HA_SOURCE_CONFIG)/custom_components/$(COMPONENT_NAME)
COMPONENT_DST := $(LOCAL_HA_CONFIG)/custom_components/$(COMPONENT_NAME)
TEST_PYTEST ?= /tmp/bereginya-aura-test-venv/bin/pytest
NODE_MODULES_STAMP := node_modules/.package-lock-stamp

.PHONY: lint test build test-e2e install-local sync-from-ha diff-ha clean release-check sync-playground sync-playground-build sync-playground-live

$(NODE_MODULES_STAMP): package.json package-lock.json
	$(NPM) ci
	mkdir -p node_modules
	touch "$(NODE_MODULES_STAMP)"

lint: $(NODE_MODULES_STAMP)
	find "$(COMPONENT_REPO_SRC)" -name '*.py' -print0 | xargs -0 -n 50 "$(PYTHON)" -m py_compile
	"$(PYTHON)" -m py_compile tests_integration/custom_components/bereginya_aura/common.py tests_integration/custom_components/bereginya_aura/conftest.py tests_integration/custom_components/bereginya_aura/test_runtime.py
	$(NPM) run typecheck
	node --check "$(COMPONENT_REPO_SRC)/frontend/bereginya-aura-card.js"

test: $(NODE_MODULES_STAMP)
	$(NPM) run check:frontend-artifacts

build: $(NODE_MODULES_STAMP)
	$(NPM) run build:frontend

sync-playground:
	node scripts/sync-playground.mjs

sync-playground-build: sync-playground build

sync-playground-live: sync-playground build install-local

test-e2e:
	PYTHONPATH="$(CURDIR)" "$(TEST_PYTEST)" \
		-c tests_integration/pytest.ini \
		tests_integration/custom_components/bereginya_aura -q

sync-from-ha:
	mkdir -p "$(dir $(COMPONENT_REPO_SRC))"
	rsync -a --delete --inplace \
		--exclude '__pycache__/' \
		--exclude '*.pyc' \
		--exclude '.DS_Store' \
		"$(COMPONENT_HA_SRC)/" "$(COMPONENT_REPO_SRC)/"

diff-ha:
	diff -qr --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' "$(COMPONENT_HA_SRC)" "$(COMPONENT_REPO_SRC)"

install-local:
	mkdir -p "$(dir $(COMPONENT_DST))"
	rsync -a --delete --inplace \
		--exclude '__pycache__/' \
		--exclude '*.pyc' \
		--exclude '.DS_Store' \
		"$(COMPONENT_REPO_SRC)/" "$(COMPONENT_DST)/"

clean:
	rm -rf node_modules
	rm -rf tests_integration/.pytest_cache

release-check: lint test build
