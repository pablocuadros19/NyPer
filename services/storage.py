"""
Capa de persistencia centralizada.
Intenta Supabase; si no está disponible, usa JSON local en data/.
Cada clave se guarda como data/{key}.json.
"""
import json
import os
import streamlit as st

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

try:
    from supabase import create_client
except ImportError:
    create_client = None


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
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def storage_set(key: str, value) -> bool:
    """Guarda un valor. Supabase si hay, siempre JSON local."""
    # Siempre guardar local
    os.makedirs(_DATA_DIR, exist_ok=True)
    path = _local_path(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False)
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
