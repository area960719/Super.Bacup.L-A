# core/retention.py
import os


class Retention:
    """Borra snapshots viejos según el límite de retención de cada tarea."""

    def __init__(self, db):
        self.db = db

    def apply(self, job_id):
        row = self.db.query("SELECT retention, dest FROM jobs WHERE id=?", (job_id,))
        if not row:
            return
        keep, dest = row[0]
        keep = keep or 10
        objs = os.path.join(dest, f"job_{job_id}", "objects")

        rows = self.db.query(
            "SELECT id FROM snapshots WHERE job_id=? AND status='ok' ORDER BY id DESC",
            (job_id,)
        )
        for (sid,) in rows[keep:]:
            for (h,) in self.db.query("SELECT hash FROM entries WHERE snapshot_id=?", (sid,)):
                self.db.execute("UPDATE objects SET refcount = refcount - 1 WHERE hash=?", (h,))
            self.db.execute("DELETE FROM entries WHERE snapshot_id=?", (sid,))
            self.db.execute("DELETE FROM snapshots WHERE id=?", (sid,))

        # Limpiar objetos huérfanos
        for (h,) in self.db.query("SELECT hash FROM objects WHERE refcount <= 0"):
            p = os.path.join(objs, h[:2], h[2:4], h)
            try:
                os.remove(p)
            except OSError:
                pass
            self.db.execute("DELETE FROM objects WHERE hash=?", (h,))
