# core/engine.py
import os
import shutil
import time
from .scanner import scan, hash_file

class BackupEngine:
    def __init__(self, db, on_progress=None):
        self.db = db
        # Función de callback para actualizar la barra de progreso en la UI (opcional por ahora)
        self.on_progress = on_progress or (lambda **kw: None)
        self._stop = False

    def stop(self):
        self._stop = True

    # --- Rutas internas del backup ---
    def _job_root(self, job):   
        return os.path.join(job['dest'], f"job_{job['id']}")
    
    def _objects(self, job):    
        return os.path.join(self._job_root(job), 'objects')
    
    def _obj_path(self, objs, h): 
        # Guarda los objetos en subcarpetas usando las primeras letras de su hash
        return os.path.join(objs, h[:2], h[2:4], h)

    # --- Decidir qué tipo de backup toca hacer ---
    def _decide_kind(self, job):
        if job['mode'] in ('incremental', 'differential'):
            return job['mode']
        # Modo 'smart': primera vez es full, después incremental
        n = self.db.query("SELECT COUNT(*) FROM snapshots WHERE job_id=? AND status='ok'", (job['id'],))[0][0]
        return 'full' if n == 0 else 'incremental'

    def _base_id(self, job, kind):
        if kind == 'incremental':
            r = self.db.query("SELECT id FROM snapshots WHERE job_id=? AND status='ok' ORDER BY id DESC LIMIT 1", (job['id'],))
            return r[0][0] if r else None
        if kind == 'differential':
            r = self.db.query("SELECT id FROM snapshots WHERE job_id=? AND kind='full' AND status='ok' ORDER BY id DESC LIMIT 1", (job['id'],))
            return r[0][0] if r else None
        return None

    # --- Motor principal ---
    def run(self, job_id):
        # 1. Buscar la configuración del trabajo en la base de datos
        row = self.db.query("SELECT id,name,source,dest,mode FROM jobs WHERE id=?", (job_id,))[0]
        job = dict(zip(['id','name','source','dest','mode'], row))

        # 2. Decidir estrategia
        kind = self._decide_kind(job)
        base_id = self._base_id(job, kind)
        if kind != 'full' and base_id is None:
            kind, base_id = 'full', None  # No hay base previa, forzamos copia completa

        # 3. Crear el snapshot en la base de datos
        cur = self.db.execute(
            "INSERT INTO snapshots(job_id, kind, base_id, created_at, status) VALUES(?,?,?,?, 'running')",
            (job_id, kind, base_id, time.strftime('%Y-%m-%d %H:%M:%S'))
        )
        snap_id = cur.lastrowid

        try:
            # 4. Ejecutar la copia real
            self._do_backup(job, snap_id, base_id)
            self.db.execute("UPDATE snapshots SET status='ok' WHERE id=?", (snap_id,))
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            self.db.execute("UPDATE jobs SET last_run=? WHERE id=?", (now, job_id))
            if kind == 'full':
                self.db.execute("UPDATE jobs SET last_full=? WHERE id=?", (now, job_id))
        except Exception as e:
            self.db.execute("UPDATE snapshots SET status='failed' WHERE id=?", (snap_id,))
            raise e

    def _do_backup(self, job, snap_id, base_id):
        source = job['source']
        objs = self._objects(job)
        os.makedirs(objs, exist_ok=True)

        # Escanear archivos actuales
        current = scan(source)

        # Índice de la base para detectar cambios (deduplicación)
        base = {}
        if base_id:
            for rel, h, size, mtime in self.db.query(
                "SELECT relpath, hash, size, mtime FROM entries WHERE snapshot_id=?", (base_id,)):
                base[rel] = (h, size, mtime)

        total = len(current)
        done = 0

        # 5. Recorrer y copiar archivo por archivo
        for rel, (size, mtime, mode) in current.items():
            if self._stop: 
                break
            done += 1
            src = os.path.join(source, rel)

            # Si el archivo no cambió, reutilizamos su hash
            prev = base.get(rel)
            if prev and prev[1] == size and abs(prev[2] - mtime) < 0.5:
                h = prev[0]
            else:
                # Si cambió, calculamos su hash y lo copiamos al pool de objetos
                h = hash_file(src)
                dst = self._obj_path(objs, h)
                if not os.path.exists(dst):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    tmp = dst + '.tmp'
                    shutil.copy2(src, tmp)  # Copia física
                    os.replace(tmp, dst)
                    self.db.execute("INSERT OR IGNORE INTO objects(hash,size,refcount) VALUES(?,?,0)", (h, size))

            # Actualizamos referencias y guardamos en la base de datos
            self.db.execute("UPDATE objects SET refcount = refcount + 1 WHERE hash=?", (h,))
            self.db.execute(
                "INSERT INTO entries(snapshot_id, relpath, hash, size, mtime, mode) VALUES(?,?,?,?,?,?)",
                (snap_id, rel, h, size, mtime, mode)
            )
            
            # Notificamos a la interfaz visual que vamos por este archivo
            self.on_progress(job=job['id'], done=done, total=total, file=rel)
