# core/scheduler.py
import threading
import time
import datetime


class Scheduler:
    """Ejecuta automáticamente las tareas programadas de los jobs."""

    def __init__(self, db, engine):
        self.db = db
        self.engine = engine
        self._stop = False
        self._fired = {}
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop = True

    def _loop(self):
        while not self._stop:
            try:
                self._tick()
            except Exception as e:
                print(f"[Scheduler] error: {e}")
            time.sleep(30)

    def _tick(self):
        now = datetime.datetime.now()
        rows = self.db.query("SELECT id, schedule FROM jobs WHERE enabled=1 AND schedule IS NOT NULL AND schedule != ''")
        for jid, sched in rows:
            if self._is_due(jid, sched, now):
                print(f"[Scheduler] Ejecutando job {jid}")
                try:
                    self.engine.run(jid)
                except Exception as e:
                    print(f"[Scheduler] Job {jid} falló: {e}")

    def _is_due(self, jid, sched, now):
        key = now.strftime("%Y-%m-%d %H:%M")
        if self._fired.get(jid) == key:
            return False

        parts = sched.strip().lower().split()
        if not parts:
            return False

        if parts[0] == "hourly" and now.minute == 0:
            self._fired[jid] = key
            return True

        if parts[0] == "daily" and len(parts) >= 2:
            try:
                hh, mm = map(int, parts[1].split(":"))
            except ValueError:
                return False
            if (now.hour, now.minute) == (hh, mm):
                self._fired[jid] = key
                return True

        if parts[0] == "weekly" and len(parts) >= 3:
            days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            if days[now.weekday()] == parts[1]:
                try:
                    hh, mm = map(int, parts[2].split(":"))
                except ValueError:
                    return False
                if (now.hour, now.minute) == (hh, mm):
                    self._fired[jid] = key
                    return True

        return False
