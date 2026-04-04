"""
Capa de persistencia centralizada (key-value).
Backend primario: Supabase (tabla nyper_storage).
Fallback: JSON local en data/ con file locking.
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
    import msvcrt

    def _lock(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock(f):
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
except ImportError:
    import fcntl

    def _lock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


@st.cache_resource
def _get_client():
    if create_client is None:
        return None
    url = ""
    key = ""
    try:
        url = st.secrets.get("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.getenv("SUPABASE_KEY", "")
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def _usa_supabase() -> bool:
    return _get_client() is not None


def _local_path(key: str) -> str:
    safe_key = key.replace("/", "_").replace("\\", "_")
    return os.path.join(_DATA_DIR, f"{safe_key}.json")


def storage_get(key: str, default=None):
    """Lee un valor. Supabase primario, JSON local fallback."""
    if _usa_supabase():
        try:
            result = _get_client().table("nyper_storage").select("value").eq("key", key).execute()
            if result.data:
                return result.data[0]["value"]
            return default
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
    """Guarda un valor. Supabase primario, JSON local siempre como backup."""
    # Supabase primario
    if _usa_supabase():
        try:
            _get_client().table("nyper_storage").upsert({
                "key": key,
                "value": value,
                "updated_at": "now()"
            }).execute()
        except Exception:
            pass

    # JSON local siempre (backup + funciona sin Supabase)
    os.makedirs(_DATA_DIR, exist_ok=True)
    path = _local_path(key)
    try:
        fd, tmp_path = tempfile.mkstemp(dir=_DATA_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
    except OSError:
        return False

    return True
