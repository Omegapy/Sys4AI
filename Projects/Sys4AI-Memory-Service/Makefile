UV ?= uv
RUN = $(UV) run --frozen

.PHONY: install validate-memory-schemas validate-memory-sources \
	validate-memory-provider validate-memory-retrieval validate-memory-security \
	validate-memory-rebuild validate-memory-integration validate-memory-evidence \
	validate-memory-minimum-risk validate-memory lint typecheck test \
	benchmark-memory-exact

install:
	$(UV) sync --locked --extra cognee --extra dev

validate-memory-schemas:
	$(RUN) pytest -q tests/contracts

validate-memory-sources:
	$(RUN) pytest -q tests/ingestion tests/exact_index

validate-memory-provider:
	$(RUN) pytest -q tests/providers

validate-memory-retrieval:
	$(RUN) pytest -q tests/retrieval

validate-memory-security:
	$(RUN) pytest -q tests/security tests/authorization tests/policies \
		tests/lifecycle tests/service tests/interfaces/test_http.py \
		tests/interfaces/test_mcp.py tests/integration

validate-memory-rebuild:
	$(RUN) pytest -q tests/rebuild tests/exchange

validate-memory-integration:
	$(RUN) pytest -q tests/integration

validate-memory-evidence:
	$(RUN) python tools/validate_release_evidence.py

validate-memory-minimum-risk:
	$(RUN) pytest -q \
		tests/integration/test_control_authority.py::test_canonical_control_reread_overrules_remembered_permission_copy \
		tests/integration/test_project_reconnect.py::test_new_agent_session_recalls_complete_current_project_context \
		tests/integration/test_multi_agent_service.py::test_two_agents_share_scoped_evidence_and_service_serializes_writes \
		tests/rebuild/test_generation_rebuild.py::test_tampered_active_pointer_is_rejected_without_path_traversal \
		tests/rebuild/test_generation_rebuild.py::test_clean_full_rebuild_restores_exact_and_provider_generations \
		tests/integration/test_lifecycle_flow.py::test_public_supersession_and_two_phase_deletion_share_governed_lifecycle \
		tests/retrieval/test_engine.py::test_hybrid_composes_channels_and_exact_identifier_stays_first

benchmark-memory-exact:
	$(RUN) python tools/benchmark_exact_index.py --fragments 100000 --batch-size 1000

lint:
	$(RUN) ruff check src tests tools

typecheck:
	$(RUN) mypy src tools

test:
	$(RUN) pytest

validate-memory: lint typecheck test validate-memory-evidence
