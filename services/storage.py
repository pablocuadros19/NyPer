"""
Capa de persistencia centralizada.
Intenta Supabase; si no está disponible, usa JSON local en data/.
Cada clave se guarda como data/{key}.json con file locking para concurrencia.
"""
import json
import os
import tempfile
import streamlit as st

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

try:
    from supabase import create_client
except ImportError:
    create_client = None

# File locking cross-platform
try:
    import msvcrt  # Windows

    def _lock(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock(f):
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
except ImportError:
    import fcntl  # Linux/Mac

    def _lock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


@st.cache_resource
def _get_client():
    if create_client is None:
        return None
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


def _local_path(key: str) -> str:
    safe_key = key.replace("/", "_").replace("\\", "_")
    return os.path.join(_DATA_DIR, f"{safe_key}.json")


def storage_get(key: str, default=None):
    """Lee un valor. Supabase si hay, si no JSON local."""
    client = _get_client()
    if client:
        try:
            result = client.table("nyper_storage").select("value").eq("key", key).execute()
            if result.data:
                return result.data[0]["value"]
        except Exception:
            pass

    # Fallback JSON local
    path = _local_path(key)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _lock(f)
                try:
                    data = json.load(f)
                finally:
                    _unlock(f)
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return default


def storage_set(key: str, value) -> bool:
    """Guarda un valor. Escritura atómica (tmp + rename) con file locking."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    path = _local_path(key)
    try:
        # Escribir a archivo temporal, después renombrar (atómico en mismo filesystem)
        fd, tmp_path = tempfile.mkstemp(dir=_DATA_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False)
            # En Windows, hay que borrar el destino antes de renombrar
            if os.path.exists(path):
                os.replace(tmp_path, path)
            else:
                os.rename(tmp_path, path)
        except Exception:
            # Limpiar temporal si falla
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
    except OSError:
        return False

    # Intentar Supabase también
    client = _get_client()
    if client:
        try:
            client.table("nyper_storage").upsert({
                "key": key,
                "value": value,
                "updated_at": "now()"
            }).execute()
        except Exception:
            pass

    return True
