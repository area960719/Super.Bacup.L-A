# core/db.py
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  source TEXT NOT NULL,
  dest TEXT NOT NULL,
  mode TEXT NOT NULL DEFAULT 'smart',
  schedule TEXT,
  enabled INTEGER DEFAULT 1,
  last_full TEXT,
  last_run TEXT,
  retention INTEGER DEFAULT 10
);

CREATE TABLE IF NOT EXISTS snapshots(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  base_id INTEGER,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entries(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL,
  relpath TEXT NOT NULL,
  hash TEXT,
  size INTEGER,
  mtime REAL,
  mode INTEGER
);

CREATE TABLE IF NOT EXISTS objects(
  hash TEXT PRIMARY KEY,
  size INTEGER,
  refcount INTEGER DEFAULT 0
);
"""

class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def execute(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()
