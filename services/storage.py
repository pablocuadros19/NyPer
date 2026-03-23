"""
Capa de persistencia centralizada — usa Supabase en la nube.
Reemplaza los archivos JSON locales de data/.
"""
import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def _get_client() -> Client:
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY", "")
    return create_client(url, key)

def storage_get(key: str, default=None):
    """Lee un valor de nyper_storage por clave. Devuelve default si no existe."""
    try:
        result = _get_client().table("nyper_storage").select("value").eq("key", key).execute()
        if result.data:
            return result.data[0]["value"]
    except Exception:
        pass
    return default

def storage_set(key: str, value) -> bool:
    """Guarda o actualiza un valor en nyper_storage."""
    try:
        _get_client().table("nyper_storage").upsert({
            "key": key,
            "value": value,
            "updated_at": "now()"
        }).execute()
        return True
    except Exception:
        return False
