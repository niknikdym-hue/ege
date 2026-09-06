"""PostgreSQL implementation that reuses the reference persistence behavior."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "peis-persistence-reference"))
from peis_persistence import PeisPersistenceStore  # noqa: E402


class _PsycopgQmarkConnection:
    """Lets reference stores keep their SQLite-style qmark SQL on PostgreSQL."""

    dialect = "postgresql"

    def __init__(self, connection: Any):
        self.connection = connection

    @staticmethod
    def _portable_sql(sql: str) -> str:
        # Reference stores intentionally use one small SQLite-compatible DDL
        # subset. PostgreSQL owns sequencing with BIGSERIAL instead of SQLite
        # AUTOINCREMENT; qmark placeholders remain translated below.
        return sql.replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT",
            "BIGSERIAL PRIMARY KEY",
        ).replace("?", "%s")

    def execute(self, sql: str, params: Any = None):
        return self.connection.execute(self._portable_sql(sql), params or ())

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        return False

    def close(self):
        self.connection.close()


class PostgresPeisPersistenceStore(PeisPersistenceStore):
    """Same public contract as PeisPersistenceStore; no SQLite fallback exists."""

    migration_versions = ("0001_peis_postgres", "0002_identity_registration_postgres")
    migration_version = migration_versions[-1]

    def __init__(self, dsn: str, *, evidence_schema: dict[str, Any], nba_schema: dict[str, Any]):
        try:
            import psycopg
            from psycopg.rows import dict_row
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL PEIS requires declared psycopg/jsonschema dependencies"
            ) from exc
        self.database_path = dsn
        self.connection = _PsycopgQmarkConnection(
            psycopg.connect(dsn, row_factory=dict_row)
        )
        self.evidence_validator = Draft202012Validator(
            evidence_schema, format_checker=FormatChecker()
        )
        self.nba_validator = Draft202012Validator(
            nba_schema, format_checker=FormatChecker()
        )
        outcome_schema = {
            "$schema": nba_schema.get(
                "$schema", "https://json-schema.org/draft/2020-12/schema"
            ),
            "$defs": nba_schema["$defs"],
            "$ref": "#/$defs/outcome_event",
        }
        self.outcome_validator = Draft202012Validator(
            outcome_schema, format_checker=FormatChecker()
        )
        self._create_schema()

    @staticmethod
    def _simple_statements(sql: str) -> list[str]:
        return [statement.strip() for statement in sql.split(";\n") if statement.strip()]

    def _apply_0001(self) -> None:
        migration = (
            HERE / "migrations" / "0001_peis_postgres.sql"
        ).read_text(encoding="utf-8")
        before, function_and_after = migration.split("CREATE OR REPLACE FUNCTION", 1)
        function_body, after = function_and_after.split("$$;", 1)
        for statement in self._simple_statements(before):
            self.connection.execute(statement)
        self.connection.execute("CREATE OR REPLACE FUNCTION" + function_body + "$$;")
        for statement in self._simple_statements(after):
            self.connection.execute(statement)

    def _apply_simple_migration(self, name: str) -> None:
        migration = (HERE / "migrations" / name).read_text(encoding="utf-8")
        for statement in self._simple_statements(migration):
            self.connection.execute(statement)

    def _create_schema(self):
        # Tracked migrations are deterministic and idempotent for empty DB/restart use.
        with self.connection:
            self._apply_0001()
            identity_migration = (
                HERE / "migrations" / "0002_identity_registration_postgres.sql"
            )
            if identity_migration.exists():
                self._apply_simple_migration(identity_migration.name)

    def readiness(self) -> bool:
        try:
            rows = self.connection.execute(
                "SELECT version FROM peis_schema_migrations WHERE version IN (%s, %s)",
                self.migration_versions,
            ).fetchall()
            return {row["version"] for row in rows} == set(self.migration_versions)
        except Exception:
            return False
