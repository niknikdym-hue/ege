"""PostgreSQL implementation that reuses the reference persistence behavior."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "peis-persistence-reference"))
from peis_persistence import PeisPersistenceStore  # noqa: E402

class _PsycopgQmarkConnection:
    """Lets inherited reference methods keep their SQLite qmark SQL unchanged."""
    def __init__(self, connection: Any): self.connection = connection
    def execute(self, sql: str, params: Any = None): return self.connection.execute(sql.replace("?", "%s"), params or ())
    def __enter__(self): self.connection.__enter__(); return self
    def __exit__(self, *args: Any): return self.connection.__exit__(*args)
    def close(self): self.connection.close()

class PostgresPeisPersistenceStore(PeisPersistenceStore):
    """Same public contract as PeisPersistenceStore; no SQLite fallback exists."""
    migration_version = "0001_peis_postgres"
    def __init__(self, dsn: str, *, evidence_schema: dict[str, Any], nba_schema: dict[str, Any]):
        try:
            import psycopg
            from psycopg.rows import dict_row
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError as exc: raise RuntimeError("PostgreSQL PEIS requires declared psycopg/jsonschema dependencies") from exc
        self.database_path = dsn
        self.connection = _PsycopgQmarkConnection(psycopg.connect(dsn, row_factory=dict_row))
        self.evidence_validator = Draft202012Validator(evidence_schema, format_checker=FormatChecker())
        self.nba_validator = Draft202012Validator(nba_schema, format_checker=FormatChecker())
        outcome_schema = {"$schema": nba_schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"), "$defs": nba_schema["$defs"], "$ref": "#/$defs/outcome_event"}
        self.outcome_validator = Draft202012Validator(outcome_schema, format_checker=FormatChecker())
        self._create_schema()
    def _create_schema(self):
        # The file is tracked, deterministic, and idempotent for empty DB/restart use.
        migration = (HERE / "migrations" / "0001_peis_postgres.sql").read_text(encoding="utf-8")
        before, function_and_after = migration.split("CREATE OR REPLACE FUNCTION", 1)
        function_body, after = function_and_after.split("$$;", 1)
        with self.connection:
            for statement in before.split(";\n"):
                if statement.strip(): self.connection.execute(statement)
            self.connection.execute("CREATE OR REPLACE FUNCTION" + function_body + "$$;")
            for statement in after.split(";\n"):
                if statement.strip(): self.connection.execute(statement)
    def readiness(self) -> bool:
        try:
            return self.connection.execute("SELECT version FROM peis_schema_migrations WHERE version = %s", (self.migration_version,)).fetchone() is not None
        except Exception: return False
