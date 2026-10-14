# main.py
import os
import sys

from core.db import DB
from core.engine import BackupEngine
from core.restore import RestoreEngine
from core.scheduler import Scheduler
from core.retention import Retention
from ui.window import MainWindow


def main():
    print("🚀 Iniciando SuperBackup...")

    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    db_path = os.path.join(base_dir, "superbackup.db")
    db = DB(db_path)
    print(f"✅ Base de datos: {db_path}")

    engine = BackupEngine(db)
    restore_engine = RestoreEngine(db)
    retention = Retention(db)

    # Aplicar retención después de cada backup
    original_run = engine.run
    def run_with_retention(job_id):
        original_run(job_id)
        try:
            retention.apply(job_id)
        except Exception as e:
            print(f"[Retention] error: {e}")
    engine.run = run_with_retention

    # Arrancar planificador
    scheduler = Scheduler(db, engine)
    print("✅ Planificador activo.")

    print("🖥️  Abriendo interfaz gráfica...")
    app = MainWindow(db, engine, restore_engine)
    app.run()

    scheduler.stop()
    print("👋 SuperBackup cerrado.")


if __name__ == "__main__":
    main()
