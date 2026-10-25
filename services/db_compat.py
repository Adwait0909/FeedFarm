"""Database compatibility helpers for Farm2Feed.

The Flask routes are written once, using MySQL-style ``%s`` placeholders and a few
SQLite date helpers.  SQLite is the default backend.  This module lets the same
routes run on MySQL and PostgreSQL by

* translating the handful of SQLite-only expressions (``date('now')``, ``datetime('now')``),
* making ``LIKE`` case-insensitive on PostgreSQL (it already is on SQLite and MySQL),
* exposing ``cursor.lastrowid`` on PostgreSQL,
* rolling back automatically after a failed statement (PostgreSQL otherwise keeps the
  transaction in an aborted state), and
* creating / upgrading the schema from ``database/schema_<dialect>.sql``.
"""
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_DATE_NOW = re.compile(r"date\(\s*'now'\s*(?:,\s*'([+-]?\d+)\s+days?'\s*)?\)", re.IGNORECASE)
_DATETIME_NOW = re.compile(r"datetime\(\s*'now'\s*\)", re.IGNORECASE)
_CURRENT_TS = re.compile(r"\bCURRENT_TIMESTAMP\b")
_LIKE = re.compile(r"\bLIKE\b", re.IGNORECASE)
_INSERT_INTO = re.compile(r"^\s*INSERT\s+INTO\s+(\w+)", re.IGNORECASE)

# Tables that own an auto-increment ``id`` column (needed to emulate lastrowid on PostgreSQL).
TABLES_WITH_ID = {
    "cows", "farmers", "farms", "doctors", "veterinary_directory",
    "farmers_assistance_requests", "veterinary_assistance_requests",
    "cow_medical_history", "found_reports",
}

PG_TIMESTAMP_TEXT = "to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')"


def translate_sql(sql, dialect):
    """Return ``sql`` rewritten for ``dialect`` ('sqlite', 'mysql' or 'postgres')."""
    if dialect == "sqlite":
        return sql

    def date_now(match):
        days = match.group(1)
        if dialect == "postgres":
            base = "CURRENT_DATE" if days is None else f"(CURRENT_DATE + INTERVAL '{int(days)} days')"
            return f"to_char({base}, 'YYYY-MM-DD')"
        base = "CURDATE()" if days is None else f"DATE_ADD(CURDATE(), INTERVAL {int(days)} DAY)"
        return f"CAST({base} AS CHAR)"

    sql = _DATE_NOW.sub(date_now, sql)
    if dialect == "postgres":
        sql = _DATETIME_NOW.sub(PG_TIMESTAMP_TEXT, sql)
        sql = _CURRENT_TS.sub(PG_TIMESTAMP_TEXT, sql)
        sql = _LIKE.sub("ILIKE", sql)
    else:
        sql = _DATETIME_NOW.sub("CAST(NOW() AS CHAR)", sql)
    return sql


def _plain_dict(row):
    if row is None or not hasattr(row, "keys"):
        return row            # plain tuple cursor (cursor() without dictionary=True)
    return dict(row)


class ServerCursor:
    """Cursor wrapper for MySQL / PostgreSQL that mirrors the SQLite wrapper in app.py."""

    def __init__(self, raw_cursor, connection, dialect):
        self._cursor = raw_cursor
        self._connection = connection
        self._dialect = dialect
        self.lastrowid = None

    def execute(self, query, params=None):
        query = translate_sql(query, self._dialect)
        wants_id = False
        if self._dialect == "postgres":
            match = _INSERT_INTO.match(query)
            if match and match.group(1).lower() in TABLES_WITH_ID and "RETURNING" not in query.upper():
                query = query.rstrip().rstrip(";") + " RETURNING id"
                wants_id = True
        try:
            self._cursor.execute(query, tuple(params) if params else None)
            if wants_id:
                row = self._cursor.fetchone()
                self.lastrowid = row["id"] if isinstance(row, dict) else row[0]
            elif self._dialect == "mysql":
                self.lastrowid = self._cursor.lastrowid
        except Exception:
            self._connection.rollback()
            raise
        return self

    def executemany(self, query, seq_of_params):
        query = translate_sql(query, self._dialect)
        try:
            return self._cursor.executemany(query, [tuple(p) for p in seq_of_params])
        except Exception:
            self._connection.rollback()
            raise

    def fetchone(self):
        return _plain_dict(self._cursor.fetchone())

    def fetchall(self):
        return [_plain_dict(row) for row in self._cursor.fetchall()]

    def close(self):
        return self._cursor.close()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class ServerConnection:
    """Connection wrapper exposing the DB-API subset the Flask routes use."""

    def __init__(self, raw_connection, dialect):
        self._conn = raw_connection
        self.dialect = dialect

    def cursor(self, dictionary=False):
        if self.dialect == "postgres":
            if dictionary:
                from psycopg2.extras import RealDictCursor
                raw = self._conn.cursor(cursor_factory=RealDictCursor)
            else:
                raw = self._conn.cursor()
        else:
            raw = self._conn.cursor(dictionary=bool(dictionary), buffered=True)
        return ServerCursor(raw, self, self.dialect)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        try:
            return self._conn.rollback()
        except Exception:  # connection already closed
            return None

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


class SchemaAdapter:
    """Gives ``seed_default_data`` the small sqlite3-like API it was written against."""

    def __init__(self, raw_connection, dialect):
        self._conn = raw_connection
        self._dialect = dialect
        self._cursor = raw_connection.cursor()

    def _prepare(self, sql):
        return translate_sql(sql.replace("?", "%s"), self._dialect)

    def execute(self, sql, params=()):
        self._cursor.execute(self._prepare(sql), tuple(params) if params else None)
        return self._cursor

    def executemany(self, sql, rows):
        self._cursor.executemany(self._prepare(sql), [tuple(r) for r in rows])
        return self._cursor

    def commit(self):
        self._conn.commit()


_COLUMN_LINE = re.compile(
    r"^\s{4}(\w+)\s+((?:SERIAL|INTEGER|INT|TEXT|DOUBLE(?: PRECISION)?|VARCHAR\(\d+\))(?=[\s,]|$).*?),?$"
)
_SCHEMA_READY = set()


def _split_statements(text):
    statements, current = [], []
    for line in text.splitlines():
        if line.strip().startswith("--"):
            continue
        current.append(line)
        if line.rstrip().endswith(";"):
            statements.append("\n".join(current).strip().rstrip(";"))
            current = []
    return [s for s in statements if s]


def _existing_columns(raw, dialect, table):
    cursor = raw.cursor()
    if dialect == "postgres":
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = %s", (table,))
    else:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s", (table,))
    names = {str(row[0]).lower() for row in cursor.fetchall()}
    cursor.close()
    return names


def _add_missing_columns(raw, dialect, statements):
    """Upgrade tables created by an older schema: add columns that are missing, never drop or alter."""
    for statement in statements:
        match = re.match(r"CREATE TABLE IF NOT EXISTS (\w+)", statement)
        if not match:
            continue
        table = match.group(1)
        existing = _existing_columns(raw, dialect, table)
        for line in statement.splitlines()[1:]:
            column = _COLUMN_LINE.match(line)
            if not column:
                continue
            name, definition = column.groups()
            if name.lower() in existing or name.lower() == "id":
                continue
            definition = re.sub(r"\s+(PRIMARY KEY|UNIQUE|NOT NULL)\b", "", definition)
            cursor = raw.cursor()
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
            cursor.close()
            raw.commit()
            logger.info("Added missing column %s.%s", table, name)


def ensure_server_schema(raw_connection, dialect, base_dir, seed_callback=None):
    """Create (or top up) the Farm2Feed tables on MySQL / PostgreSQL. Idempotent; once per process."""
    if dialect in _SCHEMA_READY:
        return
    schema_path = Path(base_dir) / "database" / f"schema_{dialect}.sql"
    statements = _split_statements(schema_path.read_text(encoding="utf-8"))
    tables = [s for s in statements if s.startswith("CREATE TABLE")]
    others = [s for s in statements if not s.startswith("CREATE TABLE")]
    cursor = raw_connection.cursor()

    def run(statement):
        try:
            cursor.execute(statement)
            raw_connection.commit()
        except Exception as error:
            raw_connection.rollback()
            # MySQL has no CREATE INDEX IF NOT EXISTS: 1061 = duplicate key name -> already created.
            if dialect == "mysql" and getattr(error, "errno", None) == 1061:
                return
            raise

    for statement in tables:
        run(statement)
    # Databases created by an older schema get their missing columns before the indexes that use them.
    _add_missing_columns(raw_connection, dialect, tables)
    for statement in others:
        run(statement)
    cursor.close()
    if seed_callback is not None:
        seed_callback(SchemaAdapter(raw_connection, dialect))
    _SCHEMA_READY.add(dialect)
