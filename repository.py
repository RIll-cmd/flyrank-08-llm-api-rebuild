import os
import sqlite3
from contextlib import contextmanager

class Repository:
    @contextmanager
    def connect(self):
        db = sqlite3.connect(os.getenv("TASK_DB", "tasks.db"))
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()
    def initialize(self):
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS initialization (id INTEGER PRIMARY KEY)")
            if not db.execute("SELECT id FROM initialization WHERE id = 1").fetchone():
                if not db.execute('SELECT 1 FROM tasks LIMIT 1').fetchone():
                    db.executemany("INSERT INTO tasks (title) VALUES (?)", [("Learn APIs",), ("Read a book",), ("Take a walk",)])
                db.execute("INSERT INTO initialization VALUES (1)")
    def convert(self, row): return {"id": row["id"], "title": row["title"], "done": bool(row["done"])} if row else None
    def list(self):
        with self.connect() as db: return [self.convert(r) for r in db.execute("SELECT * FROM tasks ORDER BY id")]
    def get(self, task_id):
        with self.connect() as db: return self.convert(db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())
    def create(self, title):
        with self.connect() as db:
            cursor = db.execute("INSERT INTO tasks (title) VALUES (?)", (title,)); return self.convert(db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone())
    def update(self, task_id, changes):
        with self.connect() as db:
            old = self.convert(db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())
            if not old: return None
            old.update(changes); db.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (old["title"], old["done"], task_id)); return old
    def delete(self, task_id):
        with self.connect() as db: return db.execute("DELETE FROM tasks WHERE id = ?", (task_id,)).rowcount > 0
