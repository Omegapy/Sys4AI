"""Transactional SQLite exact table and FTS5 lexical index."""

# Dynamic SQL below interpolates only column names and clauses selected from
# closed module-owned maps; every caller value remains a bound parameter.
# ruff: noqa: S608

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue

from sys4ai_memory.contracts import (
    AuthorityTier,
    RecordStatus,
)
from sys4ai_memory.contracts.enums import CoreRecordType
from sys4ai_memory.contracts.models import (
    LifecycleMetadata,
    MemoryRecord,
    RetrievalAuthority,
    RetrievalLifecycle,
    RetrievalScores,
    RetrievalSource,
    RetrievedRecord,
)
from sys4ai_memory.ingestion.models import NormalizedDocument
from sys4ai_memory.sources.discovery import DiscoveryReport
from sys4ai_memory.util.time import ensure_utc, utc_now

from .models import (
    ExclusionExplanation,
    IndexGeneration,
    IndexHealth,
    IndexMutationResult,
    RebuildResult,
)

INDEX_SCHEMA_VERSION = "1.0"
_CURRENT_STATUSES = (RecordStatus.ACTIVE.value, RecordStatus.APPROVED.value)
_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9_.:@/-])([A-Za-z][A-Za-z0-9_.:@/-]*)(?![A-Za-z0-9_.:@/-])"
)
_BACKTICK_RE = re.compile(r"`([^`\r\n]+)`")
_LITERAL_PHRASE_RE = re.compile(r"(?im)^\s*literal\s+phrase\s*:\s*(.+?)\s*[.]?\s*$")


class Fts5UnavailableError(RuntimeError):
    """The platform SQLite library does not provide required FTS5 behavior."""


class ExactIndex:
    """Explicitly opened embedded index; importing this module creates no storage."""

    def __init__(self, path: Path | str) -> None:
        value = str(path)
        if value != ":memory:":
            target = Path(value)
            target.parent.mkdir(parents=True, exist_ok=True)
        self.path = value
        self._connection = sqlite3.connect(value, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if value != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._assert_fts5()
        self._create_schema()

    def __enter__(self) -> ExactIndex:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    @property
    def fts5_available(self) -> bool:
        try:
            self._connection.execute("SELECT count(*) FROM fts_records").fetchone()
        except sqlite3.Error:
            return False
        return True

    def _assert_fts5(self) -> None:
        try:
            self._connection.execute(
                "CREATE VIRTUAL TABLE temp.__sys4ai_fts5_probe USING fts5(value)"
            )
            self._connection.execute("DROP TABLE temp.__sys4ai_fts5_probe")
        except sqlite3.Error as error:
            raise Fts5UnavailableError(
                "SQLite FTS5 is required for the base lexical index"
            ) from error

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS index_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generations (
                generation_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                configuration_fingerprint TEXT NOT NULL,
                profile_versions_json TEXT NOT NULL,
                adapter_versions_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                activated_at TEXT,
                status TEXT NOT NULL CHECK(status IN ('building', 'active', 'superseded', 'failed'))
            );
            CREATE INDEX IF NOT EXISTS generations_project_status
                ON generations(project_id, status);

            CREATE TABLE IF NOT EXISTS source_revisions (
                row_id INTEGER PRIMARY KEY,
                project_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                path_or_uri TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                source_revision TEXT NOT NULL,
                source_json TEXT NOT NULL,
                canonicality TEXT NOT NULL,
                authority_tier TEXT NOT NULL,
                trust_class TEXT NOT NULL,
                generation_id TEXT NOT NULL REFERENCES generations(generation_id),
                ended_generation_id TEXT REFERENCES generations(generation_id),
                status TEXT NOT NULL,
                is_current INTEGER NOT NULL CHECK(is_current IN (0, 1)),
                UNIQUE(project_id, source_id, content_sha256, path_or_uri)
            );
            CREATE INDEX IF NOT EXISTS source_revisions_current
                ON source_revisions(project_id, source_id, is_current);

            CREATE TABLE IF NOT EXISTS records (
                row_id INTEGER PRIMARY KEY,
                project_id TEXT NOT NULL,
                record_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_revision TEXT NOT NULL,
                source_path TEXT NOT NULL,
                record_json TEXT NOT NULL,
                title TEXT NOT NULL,
                title_casefold TEXT NOT NULL,
                content TEXT NOT NULL,
                content_casefold TEXT NOT NULL,
                structured TEXT NOT NULL,
                path_casefold TEXT NOT NULL,
                labels TEXT NOT NULL,
                labels_casefold TEXT NOT NULL,
                lifecycle_status TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_to TEXT,
                canonicality TEXT NOT NULL,
                authority_tier TEXT NOT NULL,
                trust_class TEXT NOT NULL,
                generation_id TEXT NOT NULL REFERENCES generations(generation_id),
                ended_generation_id TEXT REFERENCES generations(generation_id),
                is_current INTEGER NOT NULL CHECK(is_current IN (0, 1)),
                UNIQUE(project_id, record_id, source_revision, source_path)
            );
            CREATE INDEX IF NOT EXISTS records_current
                ON records(project_id, is_current, lifecycle_status);
            CREATE INDEX IF NOT EXISTS records_source
                ON records(project_id, source_id, is_current);

            CREATE TABLE IF NOT EXISTS exact_terms (
                row_id INTEGER NOT NULL REFERENCES records(row_id) ON DELETE CASCADE,
                field_name TEXT NOT NULL,
                term_kind TEXT NOT NULL,
                value TEXT NOT NULL,
                value_casefold TEXT NOT NULL,
                priority INTEGER NOT NULL,
                UNIQUE(row_id, field_name, term_kind, value)
            );
            CREATE INDEX IF NOT EXISTS exact_terms_binary
                ON exact_terms(value, field_name, priority);
            CREATE INDEX IF NOT EXISTS exact_terms_casefold
                ON exact_terms(value_casefold, field_name, priority);

            CREATE VIRTUAL TABLE IF NOT EXISTS fts_records USING fts5(
                row_id UNINDEXED,
                project_id UNINDEXED,
                source_id UNINDEXED,
                title,
                content,
                structured,
                path,
                labels,
                tokenize = 'unicode61 remove_diacritics 2'
            );

            CREATE TABLE IF NOT EXISTS discovery_exclusions (
                project_id TEXT NOT NULL,
                path_or_uri TEXT NOT NULL,
                disposition TEXT NOT NULL,
                reason TEXT NOT NULL,
                rule_ids_json TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                PRIMARY KEY(project_id, path_or_uri)
            );
            """
        )
        self._connection.execute(
            "INSERT INTO index_metadata(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (INDEX_SCHEMA_VERSION,),
        )

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise
        else:
            self._connection.execute("COMMIT")

    def upsert_document(
        self,
        document: NormalizedDocument,
        *,
        generation_id: str | None = None,
        fault_hook: Callable[[str, int], None] | None = None,
    ) -> IndexMutationResult:
        generation = self._incremental_generation(document.source.project_id, generation_id)
        with self._transaction():
            self._ensure_generation(generation, status="active")
            return self._upsert_document(
                document,
                generation_id=generation.generation_id,
                fault_hook=fault_hook,
                allow_noop=True,
            )

    def _upsert_document(
        self,
        document: NormalizedDocument,
        *,
        generation_id: str,
        fault_hook: Callable[[str, int], None] | None,
        allow_noop: bool,
    ) -> IndexMutationResult:
        source = document.source
        if any(record.project_id != source.project_id for record in document.records):
            raise ValueError("all records must share the source project")
        if any(record.source.source_id != source.source_id for record in document.records):
            raise ValueError("all records must share the source ID")
        assert source.content_sha256 is not None
        current = self._connection.execute(
            "SELECT path_or_uri, content_sha256 FROM source_revisions "
            "WHERE project_id=? AND source_id=? AND is_current=1",
            (source.project_id, source.source_id),
        ).fetchone()
        active_count = cast(
            int,
            self._connection.execute(
                "SELECT count(*) FROM records WHERE project_id=? AND source_id=? AND is_current=1",
                (source.project_id, source.source_id),
            ).fetchone()[0],
        )
        if (
            allow_noop
            and current is not None
            and current["path_or_uri"] == source.path_or_uri
            and current["content_sha256"] == source.content_sha256
            and active_count == len(document.records)
        ):
            return IndexMutationResult(
                source.project_id,
                source.source_id,
                "unchanged",
                0,
                generation_id,
            )
        if current is None:
            action = "added"
        elif current["content_sha256"] == source.content_sha256:
            action = "moved"
        else:
            action = "changed"
        ended_at = self._generation_created_at(generation_id)
        self._connection.execute(
            "UPDATE source_revisions SET is_current=0, status='superseded', "
            "ended_generation_id=? "
            "WHERE project_id=? AND source_id=? AND is_current=1",
            (generation_id, source.project_id, source.source_id),
        )
        self._connection.execute(
            "UPDATE records SET is_current=0, lifecycle_status='superseded', "
            "valid_to=COALESCE(valid_to, ?), ended_generation_id=? "
            "WHERE project_id=? AND source_id=? AND is_current=1",
            (ended_at, generation_id, source.project_id, source.source_id),
        )
        if fault_hook is not None:
            fault_hook("after_deactivate", 0)
        revision = _source_revision(document)
        self._connection.execute(
            """
            INSERT INTO source_revisions(
                project_id, source_id, path_or_uri, content_sha256, source_revision,
                source_json, canonicality, authority_tier, trust_class, generation_id,
                status, is_current
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1)
            ON CONFLICT(project_id, source_id, content_sha256, path_or_uri) DO UPDATE SET
                source_revision=excluded.source_revision,
                source_json=excluded.source_json,
                canonicality=excluded.canonicality,
                authority_tier=excluded.authority_tier,
                trust_class=excluded.trust_class,
                generation_id=excluded.generation_id,
                status='active',
                ended_generation_id=NULL,
                is_current=1
            """,
            (
                source.project_id,
                source.source_id,
                source.path_or_uri,
                source.content_sha256,
                revision,
                source.to_stable_json(),
                source.canonicality,
                source.authority_tier.value,
                source.trust_class.value,
                generation_id,
            ),
        )
        include_artifact_content = len(document.records) == 1
        for index, record in enumerate(document.records):
            searchable_content = include_artifact_content or (
                record.record_type != CoreRecordType.SOURCE_ARTIFACT.value
            )
            self._insert_record(
                record,
                source_revision=revision,
                source_path=source.path_or_uri,
                canonicality=source.canonicality,
                generation_id=generation_id,
                include_content=searchable_content,
            )
            if fault_hook is not None:
                fault_hook("after_record", index)
        return IndexMutationResult(
            source.project_id,
            source.source_id,
            action,
            len(document.records),
            generation_id,
        )

    def _insert_record(
        self,
        record: MemoryRecord,
        *,
        source_revision: str,
        source_path: str,
        canonicality: str,
        generation_id: str,
        include_content: bool,
    ) -> None:
        labels = json.dumps(record.source.locator, ensure_ascii=False, sort_keys=True)
        structured = json.dumps(
            record.content.structured,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        search_content = record.content.exact if include_content else ""
        existing = self._connection.execute(
            "SELECT row_id FROM records WHERE project_id=? AND record_id=? "
            "AND source_revision=? AND source_path=?",
            (record.project_id, record.record_id, source_revision, source_path),
        ).fetchone()
        cursor = self._connection.execute(
            """
            INSERT INTO records(
                project_id, record_id, source_id, source_revision, source_path,
                record_json, title, title_casefold, content, content_casefold,
                structured, path_casefold, labels, labels_casefold,
                lifecycle_status, valid_from, valid_to, canonicality,
                authority_tier, trust_class, generation_id, is_current
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(project_id, record_id, source_revision, source_path) DO UPDATE SET
                record_json=excluded.record_json,
                title=excluded.title,
                title_casefold=excluded.title_casefold,
                content=excluded.content,
                content_casefold=excluded.content_casefold,
                structured=excluded.structured,
                path_casefold=excluded.path_casefold,
                labels=excluded.labels,
                labels_casefold=excluded.labels_casefold,
                lifecycle_status=excluded.lifecycle_status,
                valid_from=excluded.valid_from,
                valid_to=excluded.valid_to,
                canonicality=excluded.canonicality,
                authority_tier=excluded.authority_tier,
                trust_class=excluded.trust_class,
                generation_id=excluded.generation_id,
                ended_generation_id=NULL,
                is_current=1
            """,
            (
                record.project_id,
                record.record_id,
                record.source.source_id,
                source_revision,
                source_path,
                record.to_stable_json(),
                record.title,
                record.title.casefold(),
                search_content,
                search_content.casefold(),
                structured,
                source_path.casefold(),
                labels,
                labels.casefold(),
                record.lifecycle.status.value,
                _timestamp(record.lifecycle.valid_from),
                _timestamp(record.lifecycle.valid_to),
                canonicality,
                record.authority.tier.value,
                record.authority.trust_class.value,
                generation_id,
            ),
        )
        row_id = cast(int, existing["row_id"]) if existing is not None else cursor.lastrowid
        if row_id is None:
            raise RuntimeError("record insert did not return a row identity")
        if existing is not None:
            self._connection.execute("DELETE FROM exact_terms WHERE row_id=?", (row_id,))
            self._connection.execute("DELETE FROM fts_records WHERE row_id=?", (str(row_id),))
        exact_terms = _exact_terms(
            record,
            source_path=source_path,
            include_content=include_content,
        )
        self._connection.executemany(
            "INSERT OR IGNORE INTO exact_terms("
            "row_id, field_name, term_kind, value, value_casefold, priority"
            ") VALUES(?, ?, ?, ?, ?, ?)",
            (
                (row_id, field_name, term_kind, value, value.casefold(), priority)
                for field_name, term_kind, value, priority in exact_terms
            ),
        )
        self._connection.execute(
            "INSERT INTO fts_records("
            "row_id, project_id, source_id, title, content, structured, path, labels"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(row_id),
                record.project_id,
                record.source.source_id,
                record.title,
                search_content,
                structured,
                source_path,
                labels,
            ),
        )

    def mark_source_deleted(
        self,
        project_id: str,
        source_id: str,
        *,
        generation_id: str | None = None,
    ) -> IndexMutationResult:
        generation = self._incremental_generation(project_id, generation_id)
        with self._transaction():
            self._ensure_generation(generation, status="active")
            count = cast(
                int,
                self._connection.execute(
                    "SELECT count(*) FROM records "
                    "WHERE project_id=? AND source_id=? AND is_current=1",
                    (project_id, source_id),
                ).fetchone()[0],
            )
            self._connection.execute(
                "UPDATE source_revisions SET is_current=0, status='deleted', "
                "ended_generation_id=? "
                "WHERE project_id=? AND source_id=? AND is_current=1",
                (generation.generation_id, project_id, source_id),
            )
            self._connection.execute(
                "UPDATE records SET is_current=0, lifecycle_status='deleted', "
                "valid_to=COALESCE(valid_to, ?), ended_generation_id=? "
                "WHERE project_id=? AND source_id=? AND is_current=1",
                (
                    _timestamp(generation.created_at),
                    generation.generation_id,
                    project_id,
                    source_id,
                ),
            )
        return IndexMutationResult(
            project_id,
            source_id,
            "deleted" if count else "unchanged",
            count,
            generation.generation_id,
        )

    def supersede_records(
        self,
        *,
        project_id: str,
        prior_record_id: str,
        replacement_record_id: str,
        at: datetime | None = None,
    ) -> tuple[MemoryRecord, MemoryRecord]:
        """Atomically update current and historical lifecycle index projections."""

        if prior_record_id == replacement_record_id:
            raise ValueError("a record cannot supersede itself")
        effective_at = ensure_utc(at or utc_now())
        with self._transaction():
            rows: dict[str, sqlite3.Row] = {}
            for record_id in (prior_record_id, replacement_record_id):
                matches = self._connection.execute(
                    "SELECT * FROM records WHERE project_id=? AND record_id=? "
                    "AND is_current=1 ORDER BY row_id",
                    (project_id, record_id),
                ).fetchall()
                if len(matches) != 1:
                    raise ValueError(
                        "supersession requires exactly one current index row per record"
                    )
                rows[record_id] = matches[0]

            prior = self._record_with_index_lifecycle(rows[prior_record_id])
            replacement = self._record_with_index_lifecycle(rows[replacement_record_id])
            if (
                prior.lifecycle.status is not RecordStatus.ACTIVE
                or replacement.lifecycle.status is not RecordStatus.ACTIVE
            ):
                raise ValueError("supersession requires two active index records")

            prior_lifecycle = prior.lifecycle.model_copy(
                update={
                    "status": RecordStatus.SUPERSEDED,
                    "valid_to": effective_at,
                    "superseded_by": tuple(
                        sorted({*prior.lifecycle.superseded_by, replacement_record_id})
                    ),
                }
            )
            replacement_lifecycle = replacement.lifecycle.model_copy(
                update={
                    "supersedes": tuple(
                        sorted({*replacement.lifecycle.supersedes, prior_record_id})
                    )
                }
            )
            prior_updated = MemoryRecord.model_validate(
                {**prior.to_json_dict(), "lifecycle": prior_lifecycle.to_json_dict()}
            )
            replacement_updated = MemoryRecord.model_validate(
                {
                    **replacement.to_json_dict(),
                    "lifecycle": replacement_lifecycle.to_json_dict(),
                }
            )
            self._connection.execute(
                "UPDATE records SET record_json=?, lifecycle_status=?, valid_to=?, "
                "is_current=0 WHERE row_id=?",
                (
                    prior_updated.to_stable_json(),
                    RecordStatus.SUPERSEDED.value,
                    _timestamp(effective_at),
                    rows[prior_record_id]["row_id"],
                ),
            )
            self._connection.execute(
                "UPDATE records SET record_json=? WHERE row_id=?",
                (
                    replacement_updated.to_stable_json(),
                    rows[replacement_record_id]["row_id"],
                ),
            )
        return prior_updated, replacement_updated

    @staticmethod
    def _record_with_index_lifecycle(row: sqlite3.Row) -> MemoryRecord:
        record = MemoryRecord.model_validate_json(row["record_json"])
        lifecycle = record.lifecycle.model_copy(
            update={
                "status": RecordStatus(row["lifecycle_status"]),
                "valid_from": _parse_timestamp(row["valid_from"]),
                "valid_to": (
                    None if row["valid_to"] is None else _parse_timestamp(row["valid_to"])
                ),
            }
        )
        return MemoryRecord.model_validate(
            {**record.to_json_dict(), "lifecycle": lifecycle.to_json_dict()}
        )

    def rebuild(
        self,
        generation: IndexGeneration,
        documents: Iterable[NormalizedDocument],
        *,
        fault_hook: Callable[[str, int], None] | None = None,
    ) -> RebuildResult:
        """Build and activate a complete project generation atomically."""

        materialized = tuple(documents)
        if any(item.source.project_id != generation.project_id for item in materialized):
            raise ValueError("all rebuild documents must match the generation project")
        source_ids = tuple(item.source.source_id for item in materialized)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("rebuild documents must have unique source IDs")
        records_written = 0
        with self._transaction():
            self._ensure_generation(generation, status="building")
            self._connection.execute(
                "UPDATE source_revisions SET is_current=0, status='deleted', "
                "ended_generation_id=? "
                "WHERE project_id=? AND is_current=1",
                (generation.generation_id, generation.project_id),
            )
            self._connection.execute(
                "UPDATE records SET is_current=0, lifecycle_status='deleted', "
                "valid_to=COALESCE(valid_to, ?), ended_generation_id=? "
                "WHERE project_id=? AND is_current=1",
                (
                    _timestamp(generation.created_at),
                    generation.generation_id,
                    generation.project_id,
                ),
            )
            for index, document in enumerate(materialized):
                result = self._upsert_document(
                    document,
                    generation_id=generation.generation_id,
                    fault_hook=None,
                    allow_noop=False,
                )
                records_written += result.records_written
                if fault_hook is not None:
                    fault_hook("after_source", index)
            self._connection.execute(
                "UPDATE generations SET status='superseded' "
                "WHERE project_id=? AND status='active' AND generation_id<>?",
                (generation.project_id, generation.generation_id),
            )
            self._connection.execute(
                "UPDATE generations SET status='active', activated_at=? WHERE generation_id=?",
                (_timestamp(utc_now()), generation.generation_id),
            )
            if fault_hook is not None:
                fault_hook("before_commit", len(materialized))
        return RebuildResult(
            project_id=generation.project_id,
            generation_id=generation.generation_id,
            sources_written=len(materialized),
            records_written=records_written,
        )

    def _incremental_generation(
        self, project_id: str, generation_id: str | None
    ) -> IndexGeneration:
        generation = IndexGeneration.incremental(project_id)
        if generation_id is None or generation_id == generation.generation_id:
            return generation
        if not generation_id.startswith("gen_"):
            raise ValueError("generation_id must use the gen_ prefix")
        return IndexGeneration(
            generation_id=generation_id,
            project_id=generation.project_id,
            configuration_fingerprint=generation.configuration_fingerprint,
            profile_versions=generation.profile_versions,
            adapter_versions=generation.adapter_versions,
            created_at=generation.created_at,
        )

    def _ensure_generation(self, generation: IndexGeneration, *, status: str) -> None:
        existing = self._connection.execute(
            "SELECT project_id, configuration_fingerprint FROM generations WHERE generation_id=?",
            (generation.generation_id,),
        ).fetchone()
        if existing is not None and (
            existing["project_id"] != generation.project_id
            or existing["configuration_fingerprint"] != generation.configuration_fingerprint
        ):
            raise ValueError("generation ID is already bound to different metadata")
        self._connection.execute(
            """
            INSERT INTO generations(
                generation_id, project_id, configuration_fingerprint,
                profile_versions_json, adapter_versions_json, created_at,
                activated_at, status
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(generation_id) DO UPDATE SET
                profile_versions_json=excluded.profile_versions_json,
                adapter_versions_json=excluded.adapter_versions_json
            """,
            (
                generation.generation_id,
                generation.project_id,
                generation.configuration_fingerprint,
                json.dumps(dict(generation.profile_versions), sort_keys=True),
                json.dumps(dict(generation.adapter_versions), sort_keys=True),
                _timestamp(generation.created_at),
                _timestamp(generation.created_at) if status == "active" else None,
                status,
            ),
        )

    def _generation_created_at(self, generation_id: str) -> str:
        row = self._connection.execute(
            "SELECT created_at FROM generations WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("index generation metadata is missing")
        return cast(str, row["created_at"])

    def record_discovery_report(self, report: DiscoveryReport) -> None:
        """Persist only redacted inclusion/exclusion metadata, never source content."""

        with self._transaction():
            for decision in report.decisions:
                if decision.disposition.value == "included":
                    continue
                self._connection.execute(
                    """
                    INSERT INTO discovery_exclusions(
                        project_id, path_or_uri, disposition, reason, rule_ids_json, observed_at
                    ) VALUES(?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, path_or_uri) DO UPDATE SET
                        disposition=excluded.disposition,
                        reason=excluded.reason,
                        rule_ids_json=excluded.rule_ids_json,
                        observed_at=excluded.observed_at
                    """,
                    (
                        report.project_id,
                        decision.path_or_uri,
                        decision.disposition.value,
                        decision.reason.value,
                        json.dumps(decision.rule_ids),
                        _timestamp(report.generated_at),
                    ),
                )

    def explain_source_exclusion(
        self, project_id: str, path_or_uri: str
    ) -> ExclusionExplanation | None:
        row = self._connection.execute(
            "SELECT * FROM discovery_exclusions WHERE project_id=? AND path_or_uri=?",
            (project_id, path_or_uri),
        ).fetchone()
        if row is None:
            return None
        rule_ids_value = json.loads(row["rule_ids_json"])
        if not isinstance(rule_ids_value, list) or not all(
            isinstance(item, str) for item in rule_ids_value
        ):
            raise RuntimeError("invalid exclusion rule metadata in index")
        return ExclusionExplanation(
            project_id=row["project_id"],
            path_or_uri=row["path_or_uri"],
            disposition=row["disposition"],
            reason=row["reason"],
            rule_ids=tuple(rule_ids_value),
            observed_at=_parse_timestamp(row["observed_at"]),
        )

    def query_exact(
        self,
        *,
        project_id: str,
        query: str,
        case_sensitive: bool = True,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]:
        """Return deterministic exact matches without invoking a model."""

        if not query:
            raise ValueError("exact query must not be empty")
        if limit <= 0:
            raise ValueError("limit must be positive")
        canonical_field = _field_alias(field)
        status_sql, status_parameters = _current_filter(current_only)
        value_column = "t.value" if case_sensitive else "t.value_casefold"
        query_value = query if case_sensitive else query.casefold()
        field_sql = ""
        parameters: list[object] = [project_id, query_value]
        if canonical_field is not None:
            field_sql = " AND t.field_name=?"
            parameters.append(canonical_field)
        parameters.extend(status_parameters)
        term_rows = self._connection.execute(
            f"""
            SELECT r.*, MIN(t.priority) AS match_priority
            FROM exact_terms AS t
            JOIN records AS r ON r.row_id=t.row_id
            WHERE r.project_id=? AND {value_column}=? {field_sql} {status_sql}
            GROUP BY r.row_id
            """,
            tuple(parameters),
        ).fetchall()
        candidates: dict[int, tuple[sqlite3.Row, int, str]] = {
            cast(int, row["row_id"]): (row, cast(int, row["match_priority"]), "indexed_term")
            for row in term_rows
        }

        search_columns = _substring_columns(canonical_field)
        if search_columns:
            if case_sensitive:
                clauses = [f"instr({column}, ?) > 0" for column in search_columns]
                substring_value = query
            else:
                clauses = [
                    f"instr({column}, ?) > 0" for column in _casefold_columns(search_columns)
                ]
                substring_value = query.casefold()
            substring_parameters: list[object] = [project_id]
            substring_parameters.extend(substring_value for _ in clauses)
            substring_parameters.extend(status_parameters)
            rows = self._connection.execute(
                f"SELECT r.*, 70 AS match_priority FROM records AS r "
                f"WHERE r.project_id=? AND ({' OR '.join(clauses)}) {status_sql}",
                tuple(substring_parameters),
            ).fetchall()
            for row in rows:
                row_id = cast(int, row["row_id"])
                candidates.setdefault(row_id, (row, 70, "literal_substring"))

        ordered = sorted(
            candidates.values(),
            key=lambda item: (
                item[1],
                _canonical_rank(item[0]["canonicality"]),
                _authority_rank(item[0]["authority_tier"]),
                len(cast(str, item[0]["content"])),
                item[0]["record_id"],
            ),
        )[:limit]
        return tuple(
            self._retrieved_record(
                row,
                exact_score=1.0,
                lexical_score=0.0,
                final_score=1.0,
                reason=f"exact {match_kind} match in project {project_id}",
                phrase=query if " " in query else None,
            )
            for row, _, match_kind in ordered
        )

    def query_lexical(
        self,
        *,
        project_id: str,
        query: str,
        phrase: bool = False,
        prefix: bool = False,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]:
        """Run token, phrase, prefix, or field-scoped FTS5 retrieval."""

        if not query.strip():
            raise ValueError("lexical query must not be blank")
        if phrase and prefix:
            raise ValueError("phrase and prefix modes are mutually exclusive")
        if limit <= 0:
            raise ValueError("limit must be positive")
        fts_field = _fts_field(field)
        expression = _fts_expression(query, phrase=phrase, prefix=prefix)
        if fts_field is not None:
            expression = f"{fts_field}:{expression}"
        status_sql, status_parameters = _current_filter(current_only)
        rows = self._connection.execute(
            f"""
            SELECT r.*, bm25(fts_records, 0.0, 0.0, 0.0, 4.0, 1.0, 1.5, 2.0, 2.0)
                AS lexical_rank
            FROM fts_records
            JOIN records AS r ON r.row_id=CAST(fts_records.row_id AS INTEGER)
            WHERE fts_records MATCH ? AND r.project_id=? {status_sql}
            ORDER BY lexical_rank ASC, r.row_id ASC
            LIMIT ?
            """,
            (expression, project_id, *status_parameters, limit),
        ).fetchall()
        results: list[RetrievedRecord] = []
        for row in rows:
            rank = abs(float(row["lexical_rank"]))
            lexical_score = 1.0 / (1.0 + rank)
            record = MemoryRecord.model_validate_json(row["record_json"])
            exact_score = (
                1.0
                if query.casefold() in (record.title + "\n" + record.content.exact).casefold()
                else 0.0
            )
            final_score = 1.0 if exact_score else lexical_score
            results.append(
                self._retrieved_record(
                    row,
                    exact_score=exact_score,
                    lexical_score=lexical_score,
                    final_score=final_score,
                    reason=(
                        f"lexical {'phrase' if phrase else 'prefix' if prefix else 'token'} "
                        f"match in project {project_id}"
                    ),
                    phrase=query if phrase or exact_score else None,
                )
            )
        results.sort(
            key=lambda item: (
                -item.scores.exact,
                -item.scores.lexical,
                _authority_rank(item.authority.tier.value),
                item.record_id,
            )
        )
        return tuple(results[:limit])

    def current_source_records(
        self,
        *,
        project_id: str,
        source_id: str,
    ) -> tuple[MemoryRecord, ...]:
        """Return current hydrated records for deterministic revision assignment."""

        rows = self._connection.execute(
            "SELECT record_id, source_revision, source_path FROM records "
            "WHERE project_id=? AND source_id=? AND is_current=1 "
            "ORDER BY record_id ASC",
            (project_id, source_id),
        ).fetchall()
        records: list[MemoryRecord] = []
        for row in rows:
            record = self.resolve_record(
                project_id=project_id,
                record_id=cast(str, row["record_id"]),
                source_revision=cast(str, row["source_revision"]),
                source_path=cast(str, row["source_path"]),
            )
            if record is None:
                raise RuntimeError("current exact-index record could not be hydrated")
            records.append(record)
        return tuple(records)

    def search(
        self,
        *,
        project_id: str,
        query: str,
        mode: str = "exact",
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]:
        if mode in {"exact", "exact_only"}:
            return self.query_exact(
                project_id=project_id,
                query=query,
                current_only=current_only,
                limit=limit,
            )
        if mode == "lexical":
            return self.query_lexical(
                project_id=project_id,
                query=query,
                current_only=current_only,
                limit=limit,
            )
        raise ValueError("exact index supports exact, exact_only, and lexical modes")

    def resolve_record(
        self,
        *,
        project_id: str,
        record_id: str,
        source_revision: str,
        source_path: str,
    ) -> MemoryRecord | None:
        """Hydrate one exact match for downstream namespace and policy filtering."""

        row = self._connection.execute(
            "SELECT record_json, lifecycle_status, valid_from, valid_to FROM records "
            "WHERE project_id=? AND record_id=? "
            "AND source_revision=? AND source_path=?",
            (project_id, record_id, source_revision, source_path),
        ).fetchone()
        if row is None:
            return None
        record = MemoryRecord.model_validate_json(row["record_json"])
        values = record.to_json_dict()
        lifecycle = cast(dict[str, object], values["lifecycle"])
        lifecycle["status"] = row["lifecycle_status"]
        lifecycle["valid_from"] = row["valid_from"]
        lifecycle["valid_to"] = row["valid_to"]
        record = MemoryRecord.model_validate(values)
        if (
            record.project_id != project_id
            or record.record_id != record_id
            or (record.source.path or record.source.origin_uri) != source_path
        ):
            raise RuntimeError("stored exact record identity does not match its index row")
        return record

    def resolve_lifecycle(
        self,
        *,
        project_id: str,
        record_id: str,
    ) -> LifecycleMetadata | None:
        """Resolve the newest deterministic lifecycle projection for a record."""

        row = self._connection.execute(
            "SELECT * FROM records WHERE project_id=? AND record_id=? "
            "ORDER BY is_current DESC, row_id DESC LIMIT 1",
            (project_id, record_id),
        ).fetchone()
        if row is None:
            return None
        return self._record_with_index_lifecycle(row).lifecycle

    def _retrieved_record(
        self,
        row: sqlite3.Row,
        *,
        exact_score: float,
        lexical_score: float,
        final_score: float,
        reason: str,
        phrase: str | None,
    ) -> RetrievedRecord:
        record = MemoryRecord.model_validate_json(row["record_json"])
        locator = dict(record.source.locator)
        locator["source_revision"] = cast(str, row["source_revision"])
        if phrase is not None and phrase.casefold() in record.content.exact.casefold():
            locator["label"] = f"literal phrase: {phrase}"
        return RetrievedRecord(
            record_id=record.record_id,
            record_type=record.record_type,
            title=record.title,
            content=record.content.exact,
            source=RetrievalSource(
                source_id=record.source.source_id,
                path=record.source.path,
                origin_uri=record.source.origin_uri,
                git_commit=record.source.git_commit,
                content_sha256=record.source.content_sha256,
                locator=locator,
            ),
            authority=RetrievalAuthority(
                tier=record.authority.tier,
                trust_class=record.authority.trust_class,
            ),
            lifecycle=RetrievalLifecycle(status=RecordStatus(row["lifecycle_status"])),
            scores=RetrievalScores(
                exact=exact_score,
                lexical=lexical_score,
                semantic=0.0,
                graph=0.0,
                temporal=0.0,
                trust=1.0,
                freshness=1.0,
                authority_boost=0.0,
                duplicate_penalty=0.0,
                superseded_penalty=0.0,
                scope_distance_penalty=0.0,
                unverified_penalty=0.0,
                final=final_score,
            ),
            selection_reason=(reason, "exact index did not invoke an LLM"),
        )

    def health(self, project_id: str) -> IndexHealth:
        generation = self._connection.execute(
            "SELECT generation_id FROM generations WHERE project_id=? AND status='active' "
            "ORDER BY activated_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        source_count = cast(
            int,
            self._connection.execute(
                "SELECT count(*) FROM source_revisions WHERE project_id=? AND is_current=1",
                (project_id,),
            ).fetchone()[0],
        )
        record_count = cast(
            int,
            self._connection.execute(
                "SELECT count(*) FROM records WHERE project_id=? AND is_current=1",
                (project_id,),
            ).fetchone()[0],
        )
        return IndexHealth(
            schema_version=INDEX_SCHEMA_VERSION,
            fts5_available=self.fts5_available,
            active_generation_id=generation["generation_id"] if generation is not None else None,
            current_source_count=source_count,
            current_record_count=record_count,
        )

    def source_history(self, project_id: str, source_id: str) -> tuple[Mapping[str, Any], ...]:
        rows = self._connection.execute(
            "SELECT source_id, path_or_uri, content_sha256, source_revision, status, "
            "is_current, generation_id, ended_generation_id FROM source_revisions "
            "WHERE project_id=? AND source_id=? ORDER BY row_id",
            (project_id, source_id),
        ).fetchall()
        return tuple(dict(row) for row in rows)


def _source_revision(document: NormalizedDocument) -> str:
    assert document.source.content_sha256 is not None
    return f"sha256:{document.source.content_sha256}"


def _timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return ensure_utc(value).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _exact_terms(
    record: MemoryRecord,
    *,
    source_path: str,
    include_content: bool,
) -> tuple[tuple[str, str, str, int], ...]:
    terms: set[tuple[str, str, str, int]] = {
        ("record_id", "identifier", record.record_id, 0),
        ("source.source_id", "identifier", record.source.source_id, 0),
        ("source.content_sha256", "hash", record.source.content_sha256, 0),
        ("source.path", "path", source_path, 0),
        ("title", "label", record.title, 10),
    }
    label = record.source.locator.get("label")
    if isinstance(label, str) and label:
        terms.add(("source.locator", "label", label, 10))
    for field_name, value in _flatten_json(record.content.structured, "content.structured"):
        if len(value) <= 4096:
            terms.add((field_name, "structured_value", value, 20))
        leaf = field_name.rsplit(".", 1)[-1]
        terms.add(("content.structured.key", "schema_key", leaf, 15))
    searchable = record.title
    if include_content:
        searchable += "\n" + record.content.exact
    for identifier in _IDENTIFIER_RE.findall(searchable):
        if len(identifier) <= 255:
            terms.add(("content.exact", "identifier", identifier, 30))
    if include_content:
        for phrase in _BACKTICK_RE.findall(record.content.exact):
            if 0 < len(phrase) <= 4096:
                terms.add(("content.exact", "literal", phrase, 25))
        for match in _LITERAL_PHRASE_RE.finditer(record.content.exact):
            phrase = match.group(1).rstrip(".").strip()
            if 0 < len(phrase) <= 4096:
                terms.add(("content.exact", "literal_phrase", phrase, 20))
        if len(record.content.exact) <= 4096:
            terms.add(("content.exact", "literal", record.content.exact, 40))
    return tuple(sorted(terms, key=lambda item: (item[3], item[0], item[2], item[1])))


def _flatten_json(value: JsonValue, prefix: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key in sorted(value):
            child_prefix = f"{prefix}.{key}"
            yield from _flatten_json(value[key], child_prefix)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _flatten_json(item, f"{prefix}.{index}")
    elif value is None:
        yield prefix, "null"
    elif isinstance(value, bool):
        yield prefix, "true" if value else "false"
    else:
        yield prefix, str(value)


def _current_filter(current_only: bool) -> tuple[str, tuple[object, ...]]:
    if not current_only:
        return "", ()
    return "AND r.is_current=1 AND r.lifecycle_status IN (?, ?)", _CURRENT_STATUSES


def _field_alias(field: str | None) -> str | None:
    if field is None:
        return None
    return {
        "path": "source.path",
        "source_id": "source.source_id",
        "hash": "source.content_sha256",
        "label": "source.locator",
        "code_symbol": "content.structured.symbol",
        "schema_key": "content.structured.schema_key",
        "content": "content.exact",
    }.get(field, field)


def _substring_columns(field: str | None) -> tuple[str, ...]:
    if field is None:
        return ("r.title", "r.content", "r.source_path", "r.labels")
    return {
        "title": ("r.title",),
        "content.exact": ("r.content",),
        "source.path": ("r.source_path",),
        "source.locator": ("r.labels",),
        "source.source_id": (),
        "source.content_sha256": (),
    }.get(field, ())


def _casefold_columns(columns: tuple[str, ...]) -> tuple[str, ...]:
    mapping = {
        "r.title": "r.title_casefold",
        "r.content": "r.content_casefold",
        "r.source_path": "r.path_casefold",
        "r.labels": "r.labels_casefold",
    }
    return tuple(mapping[column] for column in columns)


def _fts_field(field: str | None) -> str | None:
    if field is None:
        return None
    aliases = {
        "title": "title",
        "content": "content",
        "content.exact": "content",
        "structured": "structured",
        "content.structured": "structured",
        "path": "path",
        "source.path": "path",
        "label": "labels",
        "source.locator": "labels",
    }
    if field not in aliases:
        raise ValueError(f"unsupported lexical field: {field}")
    return aliases[field]


def _fts_expression(query: str, *, phrase: bool, prefix: bool) -> str:
    if phrase:
        return f'"{query.replace(chr(34), chr(34) * 2)}"'
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    if not tokens:
        raise ValueError("lexical query contains no searchable tokens")
    quoted = [f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens]
    if prefix:
        quoted = [f"{token}*" for token in quoted]
    return " AND ".join(quoted)


def _canonical_rank(value: str) -> int:
    return {
        "canonical": 0,
        "evidential": 1,
        "generated": 2,
        "episodic": 3,
        "scratch": 4,
        "excluded": 5,
    }.get(value, 6)


def _authority_rank(value: str) -> int:
    try:
        return int(AuthorityTier(value).value[1:])
    except (ValueError, IndexError):
        return 99
