import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.sqlite import SqliteStore


DB_PATH = Path(__file__).resolve().parents[3] / "database" / "agent.db"


class AgentPersistence:

    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            isolation_level=None,
            timeout=30,
        )
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")

        self.checkpointer = SqliteSaver(self.conn)
        self.store = SqliteStore(self.conn)

        self.store.setup()

    def close(self) -> None:
        self.conn.close()