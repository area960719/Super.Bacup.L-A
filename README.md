<div align="center">

# 🚀 SuperBackup

**Copias de seguridad inteligentes, incrementales y automatizadas.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

</div>

---

## 📖 ¿Qué es SuperBackup?

**SuperBackup** es una herramienta de escritorio que evoluciona el concepto de copia de archivos tradicional. Ya no se trata solo de copiar y pegar; se trata de **proteger tus datos en el tiempo**.

Olvídate de perder archivos por errores humanos, ransomware o fallos de disco. SuperBackup crea un historial de versiones de tus carpetas y te permite **volver atrás en el tiempo** con un solo clic.

## ✨ Características principales

- 🔄 **Copias Incrementales y Diferenciales:** Solo copia lo que cambió. Ahorra espacio y tiempo.
- 🗂️ **Pool de Objetos (Deduplicación):** Si un archivo no cambió, no se vuelve a copiar. Se guarda una sola vez usando su hash (SHA-256).
- 📅 **Programador de Tareas:** Configura copias automáticas (cada hora, diario, semanal).
- ⏪ **Restauración por Punto en el Tiempo:** Elige una fecha y recupera todo o solo un archivo específico.
- 🗑️ **Políticas de Retención:** Decide cuántas versiones antiguas quieres conservar.
- ⚡ **Interfaz Gráfica (GUI):** Fácil de usar, con barras de progreso y control de tareas.
- 🧠 **Base de Datos SQLite:** Catálogo rápido y ligero de todos tus backups.

## 🛠️ Tecnologías utilizadas

- **Lenguaje:** Python 3.10+
- **Base de Datos:** SQLite 3
- **Interfaz:** [PySide6 / Tkinter / CustomTkinter] *(Elige el que uses)*
- **Empaquetado:** PyInstaller (para crear el `.exe`)
- **Motor de Copia:** `shutil` + verificación por hash SHA-256

## 📂 Estructura del Proyecto

```text
superbackup/
├── main.py              # Punto de entrada
├── core/                # Lógica del negocio (Backend)
│   ├── db.py            # Conexión SQLite
│   ├── scanner.py       # Escaneo y hashing de archivos
│   ├── engine.py        # Motor de backup
│   ├── restore.py       # Motor de restauración
│   ├── scheduler.py     # Programador de tareas
│   └── retention.py     # Limpieza de versiones viejas
└── ui/                  # Interfaz visual (Frontend)
    ├── window.py        # Ventana principal
    ├── tasks_view.py    # Vista de tareas
    └── restore_view.py  # Vista de restauración
