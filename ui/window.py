# ui/window.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog


class MainWindow:
    def __init__(self, db, engine, restore_engine):
        self.db = db
        self.engine = engine
        self.restore_engine = restore_engine
        self.root = tk.Tk()
        self.root.title("SuperBackup 🚀")
        self.root.geometry("900x640")

        self.progress_var = tk.StringVar(value="Listo.")
        self._build_ui()
        self.refresh_jobs()
        self.refresh_jobs_combo()

    # ================= UI PRINCIPAL =================
    def _build_ui(self):
        header = tk.Label(self.root, text="Panel de Control de SuperBackup",
                          font=("Segoe UI", 16, "bold"))
        header.pack(pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # --- Pestaña Tareas ---
        self.tab_tasks = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tasks, text="📋 Tareas de Copia")
        self._build_tasks_tab()

        # --- Pestaña Restaurar ---
        self.tab_restore = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_restore, text="⏪ Restaurar")
        self._build_restore_tab()

        # --- Barra de estado inferior ---
        status = ttk.Frame(self.root)
        status.pack(fill="x", side="bottom")
        self.progress_bar = ttk.Progressbar(status, orient="horizontal",
                                            length=700, mode="determinate")
        self.progress_bar.pack(side="left", padx=10, pady=5)
        ttk.Label(status, textvariable=self.progress_var).pack(side="left")

    # ================= TAB TAREAS =================
    def _build_tasks_tab(self):
        toolbar = ttk.Frame(self.tab_tasks)
        toolbar.pack(fill="x", padx=5, pady=5)

        ttk.Button(toolbar, text="➕ Nueva", command=self.new_job).pack(side="left", padx=2)
        ttk.Button(toolbar, text="▶ Ejecutar ahora", command=self.run_selected_job).pack(side="left", padx=2)
        ttk.Button(toolbar, text="✏ Editar", command=self.edit_selected_job).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🗑 Eliminar", command=self.delete_selected_job).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔄 Refrescar", command=self.refresh_jobs).pack(side="left", padx=2)

        cols = ("id", "name", "source", "dest", "mode", "schedule", "last_run")
        self.jobs_tree = ttk.Treeview(self.tab_tasks, columns=cols, show="headings")
        headings = {
            "id": "ID", "name": "Nombre", "source": "Origen", "dest": "Destino",
            "mode": "Modo", "schedule": "Programación", "last_run": "Último run"
        }
        for c in cols:
            self.jobs_tree.heading(c, text=headings[c])
            self.jobs_tree.column(c, width=120, anchor="w")
        self.jobs_tree.column("id", width=40)
        self.jobs_tree.pack(expand=True, fill="both", padx=5, pady=5)

    def refresh_jobs(self):
        for i in self.jobs_tree.get_children():
            self.jobs_tree.delete(i)
        rows = self.db.query(
            "SELECT id, name, source, dest, mode, schedule, last_run FROM jobs ORDER BY id DESC")
        for r in rows:
            self.jobs_tree.insert("", "end", values=r)

    def _selected_job_id(self):
        sel = self.jobs_tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una tarea primero.")
            return None
        return int(self.jobs_tree.item(sel[0])["values"][0])

    # ================= NUEVA / EDITAR TAREA =================
    def new_job(self):
        JobDialog(self.root, self.db, on_save=self._after_job_save)

    def edit_selected_job(self):
        jid = self._selected_job_id()
        if jid:
            JobDialog(self.root, self.db, job_id=jid, on_save=self._after_job_save)

    def _after_job_save(self):
        self.refresh_jobs()
        self.refresh_jobs_combo()

    def delete_selected_job(self):
        jid = self._selected_job_id()
        if not jid:
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta tarea? (No borra los backups)"):
            return
        self.db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        self.refresh_jobs()
        self.refresh_jobs_combo()

    # ================= EJECUTAR BACKUP =================
    def run_selected_job(self):
        jid = self._selected_job_id()
        if not jid:
            return
        self.progress_var.set(f"Ejecutando tarea {jid}...")
        self.progress_bar["value"] = 0

        def progress(done, total, file, **kw):
            pct = int((done / total) * 100) if total else 0
            self.root.after(0, lambda: (
                self.progress_bar.configure(value=pct),
                self.progress_var.set(f"[{done}/{total}] {file[:60]}")
            ))

        def worker():
            try:
                self.engine.on_progress = progress
                self.engine.run(jid)
                self.root.after(0, lambda: self._after_run_ok(jid))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _after_run_ok(self, jid):
        self.progress_var.set("✅ Copia completada.")
        messagebox.showinfo("Listo", f"Tarea {jid} completada con éxito.")
        self.refresh_jobs()
        self.refresh_snapshots()

    # ================= TAB RESTAURAR =================
    def _build_restore_tab(self):
        top = ttk.Frame(self.tab_restore)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(top, text="Tarea:").pack(side="left")
        self.job_combo = ttk.Combobox(top, state="readonly", width=40)
        self.job_combo.pack(side="left", padx=5)
        self.job_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_snapshots())

        ttk.Button(top, text="🔄 Refrescar", command=self.refresh_jobs_combo).pack(side="left", padx=5)

        mid = ttk.Frame(self.tab_restore)
        mid.pack(expand=True, fill="both", padx=5, pady=5)

        # Lista de snapshots (izquierda)
        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=False)
        ttk.Label(left, text="Copias disponibles:").pack(anchor="w")
        self.snap_tree = ttk.Treeview(left, columns=("id", "kind", "date"),
                                      show="headings", height=20)
        for c, w in [("id", 40), ("kind", 80), ("date", 140)]:
            self.snap_tree.heading(c, text=c.capitalize())
            self.snap_tree.column(c, width=w)
        self.snap_tree.pack(fill="both", expand=True)
        self.snap_tree.bind("<<TreeviewSelect>>", lambda e: self.refresh_entries())

        # Lista de archivos (derecha)
        right = ttk.Frame(mid)
        right.pack(side="left", fill="both", expand=True, padx=10)
        ttk.Label(right, text="Archivos del snapshot:").pack(anchor="w")
        self.entries_tree = ttk.Treeview(right, columns=("relpath", "size"),
                                         show="headings", height=20)
        self.entries_tree.heading("relpath", text="Ruta")
        self.entries_tree.heading("size", text="Tamaño")
        self.entries_tree.column("relpath", width=350)
        self.entries_tree.column("size", width=80)
        self.entries_tree.pack(fill="both", expand=True)

        bottom = ttk.Frame(self.tab_restore)
        bottom.pack(fill="x", padx=5, pady=5)
        ttk.Button(bottom, text="⏪ Restaurar TODO a una carpeta...",
                   command=self.restore_all).pack(side="left", padx=5)
        ttk.Button(bottom, text="📄 Restaurar solo seleccionados...",
                   command=self.restore_selected).pack(side="left", padx=5)

    def refresh_jobs_combo(self):
        rows = self.db.query("SELECT id, name FROM jobs ORDER BY id DESC")
        self.job_combo["values"] = [f"{r[0]} - {r[1]}" for r in rows]
        if rows and not self.job_combo.get():
            self.job_combo.current(0)
        self.refresh_snapshots()

    def _current_restore_job_id(self):
        val = self.job_combo.get()
        if not val:
            return None
        return int(val.split(" - ")[0])

    def refresh_snapshots(self):
        for i in self.snap_tree.get_children():
            self.snap_tree.delete(i)
        for i in self.entries_tree.get_children():
            self.entries_tree.delete(i)
        jid = self._current_restore_job_id()
        if not jid:
            return
        for sid, kind, date, status in self.restore_engine.list_snapshots(jid):
            if status == "ok":
                self.snap_tree.insert("", "end", values=(sid, kind, date))

    def refresh_entries(self):
        for i in self.entries_tree.get_children():
            self.entries_tree.delete(i)
        sel = self.snap_tree.selection()
        if not sel:
            return
        sid = int(self.snap_tree.item(sel[0])["values"][0])
        for rel, h, size, mtime, mode in self.restore_engine.list_entries(sid):
            self.entries_tree.insert("", "end", values=(rel, size))

    def _selected_snap_id(self):
        sel = self.snap_tree.selection()
        if not sel:
            return None
        return int(self.snap_tree.item(sel[0])["values"][0])

    def restore_all(self):
        self._do_restore(only=None)

    def restore_selected(self):
        sel = self.entries_tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona al menos un archivo.")
            return
        files = [self.entries_tree.item(i)["values"][0] for i in sel]
        self._do_restore(only=files)

    def _do_restore(self, only):
        jid = self._current_restore_job_id()
        sid = self._selected_snap_id()
        if not jid or not sid:
            messagebox.showwarning("Aviso", "Selecciona una tarea y una copia.")
            return
        target = filedialog.askdirectory(title="Carpeta destino para la restauración")
        if not target:
            return

        def progress(done, total, file, **kw):
            pct = int((done / total) * 100) if total else 0
            self.root.after(0, lambda: (
                self.progress_bar.configure(value=pct),
                self.progress_var.set(f"[{done}/{total}] {file[:60]}")
            ))

        def worker():
            try:
                self.restore_engine.on_progress = progress
                self.restore_engine.restore(jid, sid, target, only=only)
                self.root.after(0, lambda: messagebox.showinfo(
                    "Listo", f"Restauración completada en:\n{target}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    # ================= LOOP =================
    def run(self):
        self.root.mainloop()


# ================= DIÁLOGO DE TAREA =================
class JobDialog:
    def __init__(self, parent, db, job_id=None, on_save=None):
        self.db = db
        self.job_id = job_id
        self.on_save = on_save

        self.top = tk.Toplevel(parent)
        self.top.title("Tarea de Backup")
        self.top.geometry("520x360")
        self.top.transient(parent)
        self.top.grab_set()

        self.name_var = tk.StringVar()
        self.src_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="smart")
        self.sched_var = tk.StringVar()
        self.retention_var = tk.StringVar(value="10")

        self._build()
        if job_id:
            self._load()

    def _build(self):
        frm = ttk.Frame(self.top, padding=15)
        frm.pack(fill="both", expand=True)

        def row(label, widget):
            ttk.Label(frm, text=label, width=16).pack(anchor="w", pady=3)
            widget.pack(fill="x", pady=2)

        row("Nombre:", ttk.Entry(frm, textvariable=self.name_var))

        src_frame = ttk.Frame(frm); src_frame.pack(fill="x", pady=3)
        ttk.Label(src_frame, text="Origen:", width=16).pack(side="left")
        ttk.Entry(src_frame, textvariable=self.src_var).pack(side="left", fill="x", expand=True)
        ttk.Button(src_frame, text="...", width=3, command=self._pick_src).pack(side="left")

        dest_frame = ttk.Frame(frm); dest_frame.pack(fill="x", pady=3)
        ttk.Label(dest_frame, text="Destino:", width=16).pack(side="left")
        ttk.Entry(dest_frame, textvariable=self.dest_var).pack(side="left", fill="x", expand=True)
        ttk.Button(dest_frame, text="...", width=3, command=self._pick_dest).pack(side="left")

        row("Modo:", ttk.Combobox(frm, textvariable=self.mode_var, state="readonly",
                                  values=["smart", "incremental", "differential"]))

        ttk.Label(frm, text="Programación (opcional):", width=30).pack(anchor="w", pady=(8, 0))
        ttk.Label(frm, text="Ejemplos: 'hourly' | 'daily 22:00' | 'weekly mon 03:00'",
                  font=("Segoe UI", 8, "italic")).pack(anchor="w")
        ttk.Entry(frm, textvariable=self.sched_var).pack(fill="x", pady=2)

        row("Retención (nº copias):", ttk.Entry(frm, textvariable=self.retention_var))

        btns = ttk.Frame(frm); btns.pack(pady=15)
        ttk.Button(btns, text="Guardar", command=self._save).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancelar", command=self.top.destroy).pack(side="left", padx=5)

    def _pick_src(self):
        d = filedialog.askdirectory(title="Carpeta origen")
        if d: self.src_var.set(d)

    def _pick_dest(self):
        d = filedialog.askdirectory(title="Carpeta destino (disco externo idealmente)")
        if d: self.dest_var.set(d)

    def _load(self):
        r = self.db.query("SELECT name, source, dest, mode, schedule, retention FROM jobs WHERE id=?",
                          (self.job_id,))[0]
        self.name_var.set(r[0]); self.src_var.set(r[1]); self.dest_var.set(r[2])
        self.mode_var.set(r[3]); self.sched_var.set(r[4] or "")
        self.retention_var.set(str(r[5] or 10))

    def _save(self):
        name = self.name_var.get().strip()
        src = self.src_var.get().strip()
        dest = self.dest_var.get().strip()
        if not name or not src or not dest:
            messagebox.showwarning("Faltan datos", "Nombre, origen y destino son obligatorios.")
            return
        try:
            retention = int(self.retention_var.get() or 10)
        except ValueError:
            retention = 10

        if self.job_id:
            self.db.execute(
                "UPDATE jobs SET name=?, source=?, dest=?, mode=?, schedule=?, retention=? WHERE id=?",
                (name, src, dest, self.mode_var.get(), self.sched_var.get(), retention, self.job_id))
        else:
            self.db.execute(
                "INSERT INTO jobs(name, source, dest, mode, schedule, enabled, retention) VALUES(?,?,?,?,?,1,?)",
                (name, src, dest, self.mode_var.get(), self.sched_var.get(), retention))
        if self.on_save:
            self.on_save()
        self.top.destroy()
