"""
Autenticación para NyPer.
Login con dominio restringido @bpba.com.ar.
Solo admin puede crear usuarios.
"""

import hashlib
import os
import secrets
import streamlit as st

DOMINIO_PERMITIDO = "@bpba.com.ar"


def _generar_salt() -> str:
    return os.urandom(16).hex()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verificar_password(password: str, salt: str, hash_guardado: str) -> bool:
    return _hash_password(password, salt) == hash_guardado


def validar_dominio(email: str) -> bool:
    return email.strip().lower().endswith(DOMINIO_PERMITIDO)


def login(email: str, password: str) -> dict | None:
    """Intenta login. Retorna dict del usuario o None."""
    from services.db import obtener_usuario, actualizar_usuario
    from datetime import datetime

    email = email.strip().lower()
    if not validar_dominio(email):
        return None

    usuario = obtener_usuario(email)
    if not usuario:
        return None
    if not usuario["activo"]:
        return None
    if not verificar_password(password, usuario["salt"], usuario["password_hash"]):
        return None

    actualizar_usuario(email, last_login=datetime.now().isoformat())
    return usuario


def es_admin() -> bool:
    usuario = st.session_state.get("usuario")
    return usuario is not None and usuario.get("rol") == "admin"


def requiere_auth():
    """
    Muestra login si no hay sesión y hace st.stop().
    Recupera sesión persistente vía token en query params (sobrevive F5).
    Retorna el dict del usuario logueado.
    """
    if "usuario" in st.session_state and st.session_state["usuario"]:
        return st.session_state["usuario"]

    # Recuperar sesión por token en query params
    token = st.query_params.get("s")
    if token:
        from services.storage import storage_get
        from services.db import obtener_usuario
        session = storage_get(f"session_{token}")
        if session and session.get("email"):
            usuario = obtener_usuario(session["email"])
            if usuario and usuario["activo"]:
                st.session_state["usuario"] = usuario
                return usuario
        # Token inválido, limpiar
        del st.query_params["s"]

    _mostrar_login()
    st.stop()


def _mostrar_login():
    """Renderiza formulario de login a pantalla completa."""
    # CSS para centrar el login
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 3rem auto;
        padding: 2rem;
        background: #f7f9fc;
        border: 1px solid #e0e5ec;
        border-radius: 14px;
        text-align: center;
    }
    .login-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 2rem;
        color: #00A651;
        margin-bottom: 0.5rem;
    }
    .login-subtitle {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">NyPer</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Inteligencia Comercial · Banco Provincia</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email corporativo", placeholder="nombre@bpba.com.ar")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.error("Completá email y contraseña.")
                elif not validar_dominio(email):
                    st.error(f"Solo se permite acceso con email {DOMINIO_PERMITIDO}")
                else:
                    usuario = login(email, password)
                    if usuario:
                        st.session_state["usuario"] = usuario
                        st.session_state["bienvenida_pendiente"] = True
                        # Persistir sesión con token
                        token = secrets.token_urlsafe(32)
                        from services.storage import storage_set
                        storage_set(f"session_{token}", {"email": usuario["email"]})
                        st.query_params["s"] = token
                        st.rerun()
                    else:
                        st.error("Email o contraseña incorrectos, o usuario inactivo.")

        st.caption("Contactá al administrador para obtener acceso.")
