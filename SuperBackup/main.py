# main.py
# Punto de entrada de SuperBackup

import os
from core.db import DB
from core.engine import BackupEngine
from ui.window import MainWindow


def main():
    print("🚀 Iniciando SuperBackup...")

    # 1. Ruta donde se guardará la base de datos (junto al ejecutable)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "superbackup.db")

    # 2. Crear conexión a la base de datos (crea las tablas si no existen)
    db = DB(db_path)
    print(f"✅ Base de datos lista en: {db_path}")

    # 3. Crear el motor de backup
    engine = BackupEngine(db)
    print("✅ Motor de backup cargado.")

    # 4. Abrir la ventana principal (bloquea hasta que el usuario la cierre)
    print("🖥️  Abriendo interfaz gráfica...")
    app = MainWindow(db, engine)
    app.run()

    print("👋 SuperBackup cerrado.")


if __name__ == "__main__":
    main()
