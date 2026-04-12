.PHONY: help check-fast check enforce tdd test-enforcement test-skeleton test-unit test-integration scan lint

help:
	@echo "Available targets: help, check-fast, check, lint, enforce, tdd, test-enforcement, test-skeleton, test-unit, test-integration, scan"

check-fast: lint enforce tdd test-unit

check: check-fast test-integration scan test-skeleton

enforce:
	@python enforcement/deps_rules.py
	@python scripts/validate_story.py --all

tdd:
	@python enforcement/tdd_guard.py

test-enforcement:
	@python -m pytest tests/unit/test_enforcement_tools.py -q

test-skeleton:
	@python scripts/run_skeleton_tester.py

test-unit:
	@python -m pytest tests/unit -q

test-integration:
	@python -m pytest tests/integration -q

scan:
	@python enforcement/secret_scan.py

lint:
	@python -m ruff check src tests enforcement scripts
