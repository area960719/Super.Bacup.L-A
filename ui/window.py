# ui/window.py
import tkinter as tk
from tkinter import ttk, messagebox

class MainWindow:
    def __init__(self, db, engine):
        self.db = db
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("SuperBackup 🚀")
        self.root.geometry("800x600")
        
        self._build_ui()

    def _build_ui(self):
        # Título
        lbl_title = tk.Label(self.root, text="Panel de Control de SuperBackup", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        # Pestañas (Tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Pestaña 1: Tareas
        tab_tasks = ttk.Frame(notebook)
        notebook.add(tab_tasks, text="📋 Tareas de Copia")
        self._build_tasks_tab(tab_tasks)

        # Pestaña 2: Restaurar
        tab_restore = ttk.Frame(notebook)
        notebook.add(tab_restore, text="⏪ Restaurar")
        self._build_restore_tab(tab_restore)

    def _build_tasks_tab(self, parent):
        lbl = tk.Label(parent, text="Aquí irá la lista de tareas programadas.", font=("Arial", 12))
        lbl.pack(pady=20)
        
        btn = ttk.Button(parent, text="➕ Nueva Tarea (Próximamente)")
        btn.pack(pady=5)

    def _build_restore_tab(self, parent):
        lbl = tk.Label(parent, text="Aquí podrás elegir una fecha y restaurar tus archivos.", font=("Arial", 12))
        lbl.pack(pady=20)

    def run(self):
        """Arranca el bucle de la ventana."""
        self.root.mainloop()
