"""Local BM25 search memory on pure SQLite FTS5 with context management."""

import re
import sqlite3


class FtsMemory:
    """Local BM25 search memory on pure SQLite FTS5."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Acquire connection with Windows busy timeout and WAL pragmas."""
        if self._conn is not None:
            return self._conn
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        if not self.db_path.startswith(":memory:"):
            try:
                conn.execute("PRAGMA journal_mode = WAL;")
            except sqlite3.OperationalError:
                pass
        self._conn = conn
        return self._conn

    def _init_db(self) -> None:
        """Initialize FTS5 virtual table with unicode61 tokenizer."""
        conn = self._get_conn()
        with conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS session_fts USING fts5(
                    event_id,
                    source,
                    content,
                    tokenize='unicode61'
                )
            """)

    def close(self) -> None:
        """Close database connection and release file locks."""
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    def __enter__(self) -> "FtsMemory":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()

    @staticmethod
    def clean_query(query: str) -> str:
        """Sanitize query into safe quoted terms to prevent FTS5 syntax errors."""
        if not isinstance(query, str):
            return ""
        terms = re.findall(r"[\w]+", query, re.UNICODE)
        safe = [f'"{t}"' for t in terms if t.strip()]
        return " ".join(safe)

    def _exec_insert(self, eid: str, src: str, txt: str) -> bool:
        """Execute insert statement transactionally."""
        try:
            conn = self._get_conn()
            with conn:
                conn.execute(
                    "INSERT INTO session_fts(event_id, source, content) VALUES (?, ?, ?)",
                    (eid, src, txt),
                )
            return True
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return False

    def index_event(self, event_id: str, source: str, content: str) -> bool:
        """Insert event into FTS5 index transactionally."""
        if not (isinstance(event_id, str) and event_id.strip()):
            return False
        if not (isinstance(content, str) and content.strip()):
            return False
        return self._exec_insert(event_id.strip(), (source or "").strip(), content.strip())

    def search(self, query: str, limit: int = 5) -> list[dict[str, str | float]]:
        """Search events safely using BM25 ranking."""
        safe_q = self.clean_query(query)
        if not safe_q:
            return []
        bound = max(1, min(limit, 50))
        try:
            conn = self._get_conn()
            cur = conn.execute(
                "SELECT event_id, source, snippet(session_fts, 2, '<b>', '</b>', '...', 10), "
                "bm25(session_fts) as rank FROM session_fts WHERE session_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (safe_q, bound),
            )
            return [
                {
                    "event_id": str(r[0]),
                    "source": str(r[1]),
                    "snippet": str(r[2]),
                    "rank": float(r[3]),
                }
                for r in cur.fetchall()
            ]
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return []
