# core/scanner.py
import os
import hashlib

# Tamaño de lectura: 1 MB. Evita que el programa consuma toda la RAM con archivos enormes.
CHUNK = 1024 * 1024  

def hash_file(path):
    """
    Calcula la huella digital (SHA-256) de un archivo.
    Sirve para saber si un archivo cambió sin tener que copiarlo de nuevo.
    """
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                bloque = f.read(CHUNK)
                if not bloque:
                    break
                h.update(bloque)
        return h.hexdigest()
    except (OSError, PermissionError):
        # Si no se puede leer (ej: archivo bloqueado), devolvemos None
        return None

def scan(root):
    """
    Recorre una carpeta completa (incluyendo subcarpetas) y devuelve un diccionario.
    Estructura: { "ruta/relativa/archivo.txt": (tamaño, fecha_modificacion, permisos) }
    """
    out = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            try:
                st = os.stat(full)
            except OSError:
                continue
            
            # Guardamos la información clave de cada archivo
            rel_path = os.path.relpath(full, root)
            out[rel_path] = (st.st_size, st.st_mtime, st.st_mode)
            
    return out
