"""
NyPer v4.0 — Inteligencia Comercial Territorial
Banco Provincia · Multi-sucursal
Paradigma: CONTACTABILITY-FIRST / OPERATOR-FIRST
"""
import os
import json
import re
import logging
import base64
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Logging a archivo para poder seguir el progreso desde terminal
LOG_PATH = "data/nyper.log"
os.makedirs("data", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("nyper")

DATOS_DIR = "data"
HISTORIAL_DIR = "data/historial"

def img_to_base64(path):
    """Convierte imagen local a string base64 para HTML inline."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

# Logo NyPer como base64 (se usa en header y home)
_NYPER_LOGO_B64 = img_to_base64("assets/logo_nyper.png")
_NYPER_LOGO_HTML = f'<img src="data:image/png;base64,{_NYPER_LOGO_B64}" alt="NyPer">' if _NYPER_LOGO_B64 else '<span style="font-family:Montserrat,sans-serif;font-weight:900;color:#00A651">NyPer</span>'

# Firma Pablo (se usa en footer global)
_FIRMA_B64 = img_to_base64("assets/firma_pablo.png")
_FIRMA_HTML = f'<img src="data:image/png;base64,{_FIRMA_B64}" alt="@Pablocuadros19">' if _FIRMA_B64 else '<span style="font-family:serif;font-style:italic;color:#666;font-size:1rem">@Pablocuadros19</span>'

# Perrito BP (búsqueda animada)
_PERRITO_B64 = img_to_base64("assets/perrito_bp.png")
_PERRITO_HTML = f'<img src="data:image/png;base64,{_PERRITO_B64}" alt="Buscando...">' if _PERRITO_B64 else ''

# Perrito NyP (home decorativo)
_PERRITO_NYP_B64 = img_to_base64("assets/perrito_nyp.png")
_PERRITO_NYP_HTML = f'<img src="data:image/png;base64,{_PERRITO_NYP_B64}" alt="NyPer mascota">' if _PERRITO_NYP_B64 else ''

def datos_path_sucursal(codigo):
    """Ruta del archivo de leads para una sucursal específica."""
    return os.path.join(DATOS_DIR, f"prospectos_{codigo}.json")

# Cargar sucursales desde JSON oficial
SUCURSALES_JSON_PATH = "data/sucursales.json"
if os.path.exists(SUCURSALES_JSON_PATH):
    with open(SUCURSALES_JSON_PATH, "r", encoding="utf-8") as _f:
        _suc_data = json.load(_f)
    # Solo incluir sucursales con coordenadas
    _suc_data = [s for s in _suc_data if s.get("lat") is not None]
    _suc_data.sort(key=lambda s: s["codigo"])
    SUCURSALES = {
        f"{s['codigo']} — {s['nombre']}": {
            "lat": s["lat"], "lng": s["lng"],
            "dir": f"{s['domicilio']}, {s['localidad']}",
            "partido": s.get("partido", ""),
        }
        for s in _suc_data
    }
else:
    SUCURSALES = {
        "5155 — VILLA BALLESTER": {"lat": -34.5453, "lng": -58.5519, "dir": "Pacífico Rodríguez 40, Villa Ballester", "partido": "General San Martin"},
    }

SUCURSAL_DEFAULT = "5155 — VILLA BALLESTER"
from services.storage import storage_get, storage_set

def _cargar_config():
    return storage_get("config", {})

def _guardar_config(nuevos):
    cfg = _cargar_config()
    cfg.update(nuevos)
    storage_set("config", cfg)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NyPer — Inteligencia Comercial",
    page_icon="assets/logosolo_clean.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;900&display=swap');
  :root{--primary-color:#00A651!important}
  .stApp,.main,.block-container{background:#ffffff!important;color:#1a1a2e!important;font-family:'Montserrat',sans-serif!important}
  header[data-testid="stHeader"]{background:#ffffff!important}
  div[data-testid="stDecoration"]{display:none!important}
  section[data-testid="stSidebar"]{display:none!important}
  button[data-testid="stSidebarCollapsedControl"]{display:none!important}
  div[data-baseweb="select"]>div{background:#f7f9fc!important;border-color:#d0d5dd!important;color:#1a1a2e!important}
  div[data-baseweb="popover"]>div,div[data-baseweb="menu"]{background:#ffffff!important;border:1px solid #e0e5ec!important}
  div[data-baseweb="menu"] li{background:#ffffff!important;color:#1a1a2e!important}
  div[data-baseweb="menu"] li:hover{background:#f0f9f4!important}
  div[data-baseweb="tag"]{background:#e8f5ee!important;color:#00A651!important}
  input,textarea{background:#f7f9fc!important;color:#1a1a2e!important;border-color:#d0d5dd!important}
  .stMultiSelect>div>div,.stSelectbox>div>div{background:#f7f9fc!important;border-color:#d0d5dd!important}
  .stRadio label,.stCheckbox label{color:#1a1a2e!important}
  p,span,label,.stMarkdown{color:#1a1a2e!important}
  .stCaption,.stCaption p{color:#666!important}
  div[data-testid="stMetric"]{background:#f7f9fc;border:1px solid #e0e5ec;border-radius:10px;padding:1rem}
  div[data-testid="stMetric"] label{color:#666!important;font-size:.75rem!important;text-transform:uppercase}
  div[data-testid="stMetric"] div[data-testid="stMetricValue"]{color:#00A651!important;font-size:1.8rem!important;font-weight:700!important}
  .stButton>button{background:linear-gradient(180deg,#00A651 0%,#008a44 100%);color:#fff!important;border:1px solid #007a3d!important;font-weight:600;border-radius:8px;box-shadow:0 3px 8px rgba(0,166,81,.25),inset 0 1px 0 rgba(255,255,255,.15);transition:all 0.15s ease}
  .stButton>button:hover{background:linear-gradient(180deg,#00b85c 0%,#00A651 100%);box-shadow:0 5px 12px rgba(0,166,81,.35),inset 0 1px 0 rgba(255,255,255,.2);transform:translateY(-1px)}
  .stButton>button:active{transform:translateY(1px);box-shadow:inset 0 2px 4px rgba(0,0,0,.15)!important}
  .stDownloadButton>button{background:linear-gradient(180deg,#f7f9fc 0%,#e8ecf1 100%)!important;color:#00A651!important;border:1px solid #d0d5dd!important;font-weight:600;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.08),inset 0 1px 0 rgba(255,255,255,.9);transition:all 0.15s ease}
  .stDownloadButton>button:hover{background:linear-gradient(180deg,#e8f5ee 0%,#d4edda 100%)!important;border-color:#00A651!important;box-shadow:0 3px 8px rgba(0,166,81,.15),inset 0 1px 0 rgba(255,255,255,.9);transform:translateY(-1px)}
  .stDownloadButton>button:active{transform:translateY(1px);box-shadow:inset 0 2px 4px rgba(0,0,0,.1)!important}
  .stProgress>div>div{background:#e0e5ec!important}
  .stProgress>div>div>div{background:linear-gradient(90deg,#00A651,#00B8D4)!important}
  .stTabs [data-baseweb="tab-list"]{background:#ffffff;border-bottom:2px solid #e0e5ec;border-radius:0;padding:0;gap:.5rem}
  .stTabs [data-baseweb="tab"]{color:#666!important;border-radius:0;padding:.6rem 1.2rem;border-bottom:3px solid transparent;font-family:'Montserrat',sans-serif;font-weight:600;font-size:.9rem}
  .stTabs [data-baseweb="tab"]:hover{color:#00A651!important;border-bottom-color:#c8e6d5}
  .stTabs [aria-selected="true"]{background:transparent!important;color:#00A651!important;border-bottom:3px solid #00A651!important}
  hr{border-color:#e0e5ec!important}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark){background:linear-gradient(90deg,#ffffff 0%,#00A651 25%,#00B8D4 100%);border-radius:12px;padding:1rem 2rem;margin-bottom:1rem;align-items:center}
  .hdr-content{display:flex;align-items:center;gap:2rem;padding:.8rem 0}
  .hdr-content img{height:177px;margin:-20px 0}
  .hdr-content p{color:#fff!important;font-size:1.6rem;font-weight:600;margin:0 0 0 1.5rem;font-family:'Montserrat',sans-serif;letter-spacing:.5px;line-height:1.4;text-shadow:0 1px 3px rgba(0,0,0,.15)}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark) label{color:rgba(255,255,255,.9)!important;font-family:'Montserrat',sans-serif!important;font-size:.85rem!important;font-weight:600!important;letter-spacing:.5px!important}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark)>div[data-testid="stColumn"]{display:flex;align-items:center}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark) div[data-baseweb="select"]>div{background:transparent!important;color:#fff!important;border-color:rgba(255,255,255,.3)!important}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark) div[data-baseweb="select"] span{color:#fff!important;font-family:'Montserrat',sans-serif!important;font-size:.9rem!important}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark) div[data-baseweb="select"] input{background:transparent!important;color:#fff!important;font-family:'Montserrat',sans-serif!important}
  div[data-testid="stHorizontalBlock"]:has(.hdr-mark) svg{fill:#fff!important}
  .home-hero{text-align:center;padding:3rem 1rem 2rem;font-family:'Montserrat',sans-serif}
  .home-logos-row{display:flex;align-items:center;justify-content:center;gap:2rem;margin-bottom:1rem}
  .home-hero .logo-bp{height:240px;margin-bottom:0}
  .home-hero h1{font-family:'Montserrat',sans-serif;font-size:3.5rem;font-weight:900;letter-spacing:2px;margin:0;background:linear-gradient(135deg,#00A651,#00B8D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .home-hero .subtitle{font-family:'Montserrat',sans-serif;font-size:1rem;font-weight:400;color:#555!important;letter-spacing:3px;text-transform:uppercase;margin:.5rem 0 0}
  .home-hero .hero-desc{font-family:'Montserrat',sans-serif;font-size:.95rem;font-weight:300;color:#555!important;margin:1.2rem auto 0;max-width:700px;line-height:1.8}
  .home-card{background:#f7f9fc;border:1px solid #e0e5ec;border-radius:14px;padding:1.8rem 1.5rem;text-align:center;height:100%;transition:border-color .2s,box-shadow .2s;font-family:'Montserrat',sans-serif}
  .home-card:hover{border-color:#00A651;box-shadow:0 4px 20px rgba(0,132,61,.1)}
  .home-card .card-icon{font-size:2.2rem;margin-bottom:.8rem;display:flex;justify-content:center;align-items:center}
  .home-card h3{font-family:'Montserrat',sans-serif;font-size:1rem;font-weight:700;color:#1a1a2e!important;margin:0 0 .6rem}
  .home-card p{font-family:'Montserrat',sans-serif;font-size:.85rem;color:#555!important;line-height:1.6;margin:0}
  .home-section{background:#f0f9f4;border:1px solid #c8e6d5;border-left:4px solid #00A651;border-radius:12px;padding:1.8rem 2rem;font-family:'Montserrat',sans-serif;margin:1.2rem 0}
  .home-section .section-label{font-family:'Montserrat',sans-serif;font-size:.7rem;font-weight:700;color:#00A651!important;letter-spacing:2px;text-transform:uppercase;margin:0 0 .5rem}
  .home-section h3{font-family:'Montserrat',sans-serif;font-size:1.05rem;font-weight:700;color:#1a1a2e!important;margin:0 0 .6rem}
  .home-section p{font-family:'Montserrat',sans-serif;font-size:.88rem;color:#555!important;line-height:1.7;margin:0}
  .home-sources{display:flex;gap:.8rem;flex-wrap:wrap;margin-top:1rem}
  .home-sources span{font-family:'Montserrat',sans-serif;font-size:.78rem;font-weight:600;color:#00A651!important;background:#e8f5ee;padding:.35rem .9rem;border-radius:20px;border:1px solid #c8e6d5}
  .home-flow{text-align:center;font-family:'Montserrat',sans-serif;margin:1.5rem 0;padding:1.2rem;background:#f7f9fc;border-radius:12px;border:1px solid #e0e5ec}
  .home-flow .flow-label{font-size:.7rem;color:#999!important;letter-spacing:2px;text-transform:uppercase;margin-bottom:.8rem}
  .home-flow .flow-steps{font-size:.95rem;color:#333!important}
  .home-flow .flow-steps .step{color:#00A651!important;font-weight:700}
  .home-flow .flow-steps .arrow{color:#ccc!important;margin:0 .4rem}
  .home-footer{text-align:center;padding:2rem 0;border-top:1px solid #e0e5ec;margin-top:2rem;font-family:'Montserrat',sans-serif}
  .home-footer img{height:192px;margin-top:.5rem}
  .global-footer img{height:192px;margin-top:.5rem}
  .home-footer .version{font-size:.75rem;color:#999!important;margin-top:1rem}
  .home-divider{width:60px;height:3px;background:linear-gradient(90deg,#00A651,#00B8D4);margin:1rem auto;border-radius:2px}
  .perrito-buscando{text-align:center;padding:2rem}
  .perrito-buscando img{height:150px;animation:olfatear 1.5s ease-in-out infinite}
  .perrito-buscando p{font-family:'Montserrat',sans-serif;color:#555!important;font-size:.9rem;margin-top:.5rem}
  @keyframes olfatear{0%,100%{transform:translateX(0) rotate(0deg)}50%{transform:translateX(15px) rotate(-3deg)}}
  .perrito-home{text-align:center;margin:1.5rem 0}
  .perrito-home img{height:120px}
  .perrito-home p{font-family:'Montserrat',sans-serif;color:#555!important;font-size:.85rem;margin-top:.5rem;font-style:italic}
  .hero-nyper-logo{height:300px}
  .hero-perrito{height:224px;margin:0.5rem 0}
  /* ── Responsive móvil ──────────────────────────────────── */
  @media(max-width:768px){
    .home-hero{padding:1.5rem 0.5rem 1rem}
    .home-logos-row{flex-wrap:wrap;justify-content:center;gap:0.5rem}
    .home-hero .logo-bp{width:100%;height:100px!important;object-fit:contain;order:-1}
    .hero-nyper-logo{height:120px!important;order:0}
    .hero-perrito{height:100px!important;margin:0!important;order:1}
    .hdr-content{gap:0.5rem!important;padding:0.3rem 0!important}
    .hdr-content img{height:90px!important;margin:0!important}
    .hdr-content p{font-size:0.8rem!important;margin:0!important}
    .home-hero h1{font-size:2rem!important}
    .home-hero .subtitle{font-size:0.8rem;letter-spacing:1.5px}
    .home-hero .hero-desc{font-size:0.85rem}
    .home-divider{margin:0.5rem auto}
    .home-card{padding:1rem;text-align:center!important;display:flex!important;flex-direction:column!important;align-items:center!important}
    .home-card h3{font-size:0.9rem;text-align:center!important;width:100%}
    .home-card p{font-size:0.8rem;text-align:center!important;width:100%}
    .home-section{padding:1rem 1.2rem}
    .home-flow .flow-steps{font-size:0.8rem}
    .home-footer img,.global-footer img{height:100px!important}
    .perrito-buscando img{height:80px!important}
  }
</style>
""", unsafe_allow_html=True)

# ── Selector de sucursal ──────────────────────────────────────────────────────

# ── Autenticación ─────────────────────────────────────────────────────────────
from services.db import inicializar_db
from services.auth import requiere_auth, es_admin

inicializar_db()
usuario = requiere_auth()

# ── Bienvenida post-login (aparece 3 seg y se va) ───────────────────────────
if st.session_state.get("bienvenida_pendiente"):
    import random as _random, time as _time
    _frase = _random.choice([
        "Cada gestión cuenta.",
        "A hacer la diferencia.",
        "El territorio espera.",
        "Otro día para sumar valor.",
        "Vamos con todo.",
        "Un prospecto más cerca.",
        "La sucursal necesita de vos.",
    ])
    _logo_bienvenida = f'<img src="data:image/png;base64,{_NYPER_LOGO_B64}" style="height:120px;margin-bottom:2rem">' if _NYPER_LOGO_B64 else ''
    st.markdown(f"""
    <style>
    @keyframes nyp-fadeInUp {{
        0% {{ opacity:0; transform:translateY(30px) }}
        100% {{ opacity:1; transform:translateY(0) }}
    }}
    </style>
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;text-align:center;font-family:'Montserrat',sans-serif">
        <div style="opacity:0;animation:nyp-fadeInUp 1s ease-out forwards">{_logo_bienvenida}</div>
        <h1 style="font-size:2.5rem;font-weight:700;color:#1a1a2e;margin:0;opacity:0;animation:nyp-fadeInUp 1.5s ease-out forwards;animation-delay:.3s">Hola, {usuario['nombre']}</h1>
        <p style="font-size:1.1rem;color:#555;margin-top:1rem;font-weight:400;opacity:0;animation:nyp-fadeInUp 2s ease-out forwards;animation-delay:.8s">{_frase}</p>
    </div>
    """, unsafe_allow_html=True)
    _time.sleep(3)
    del st.session_state["bienvenida_pendiente"]
    st.rerun()

# ── Barra superior: usuario + cerrar sesión ──────────────────────────────────
def _cerrar_sesion():
    _token = st.query_params.get("s")
    if _token:
        storage_set(f"session_{_token}", {})
        del st.query_params["s"]
    for _k in ["usuario", "modulo_activo", "bienvenida_pendiente"]:
        st.session_state.pop(_k, None)
    st.rerun()

_top_cols = st.columns([1, 5, 2, 1]) if st.session_state.get("modulo_activo") else st.columns([6, 2, 1])
if st.session_state.get("modulo_activo"):
    with _top_cols[0]:
        if st.button("← Inicio", key="btn_volver"):
            del st.session_state["modulo_activo"]
            st.rerun()
    with _top_cols[2]:
        st.markdown(f"<p style='text-align:right;margin:0;padding-top:.4rem;font-family:Montserrat,sans-serif;font-size:.85rem;color:#555'>👤 {usuario['nombre']} {usuario['apellido']}</p>", unsafe_allow_html=True)
    with _top_cols[3]:
        if st.button("Cerrar sesión", key="btn_logout"):
            _cerrar_sesion()
else:
    with _top_cols[1]:
        st.markdown(f"<p style='text-align:right;margin:0;padding-top:.4rem;font-family:Montserrat,sans-serif;font-size:.85rem;color:#555'>👤 {usuario['nombre']} {usuario['apellido']}</p>", unsafe_allow_html=True)
    with _top_cols[2]:
        if st.button("Cerrar sesión", key="btn_logout_land"):
            _cerrar_sesion()

# ── Landing — elegir módulo ──────────────────────────────────────────────────
if not st.session_state.get("modulo_activo"):
    _logo_landing = f'<img src="data:image/png;base64,{_NYPER_LOGO_B64}" style="height:180px">' if _NYPER_LOGO_B64 else '<h1 style="font-size:3rem;font-weight:900;color:#00A651;margin:0">NyPer</h1>'
    _perrito_landing = f'<img src="data:image/png;base64,{_PERRITO_NYP_B64}" style="height:100px;margin-left:1.5rem">' if _PERRITO_NYP_B64 else ''
    st.markdown(f"""
    <div style="text-align:center;padding:3rem 1rem 1rem;font-family:'Montserrat',sans-serif">
        <div style="display:flex;align-items:center;justify-content:center">{_logo_landing}{_perrito_landing}</div>
        <p style="font-size:1rem;color:#555;letter-spacing:3px;text-transform:uppercase;margin-top:.5rem">Inteligencia Comercial Territorial</p>
        <div style="width:60px;height:3px;background:linear-gradient(90deg,#00A651,#00B8D4);margin:1rem auto;border-radius:2px"></div>
        <p style="font-size:.95rem;color:#666;margin-top:.5rem">¿Qué querés hacer hoy, {usuario['nombre']}?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<style>
    .main .stButton > button {
        font-size: 1.3rem !important;
        padding: 1.2rem 2rem !important;
        min-height: 70px !important;
    }
    </style>""", unsafe_allow_html=True)

    _lc1, _lc2 = st.columns(2)
    with _lc1:
        st.markdown("""
        <div style="background:#f7f9fc;border:1px solid #e0e5ec;border-radius:14px;padding:2rem 1.5rem;text-align:center;font-family:'Montserrat',sans-serif;margin-bottom:1rem">
            <div style="font-size:3rem;margin-bottom:1rem">🔍</div>
            <h3 style="font-size:1.1rem;font-weight:700;color:#1a1a2e;margin:0 0 .5rem">Buscar Clientes</h3>
            <p style="font-size:.85rem;color:#555;line-height:1.6;margin:0">Descubrir, enriquecer y gestionar<br>prospectos en tu zona</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Buscar Clientes", key="landing_nyper", use_container_width=True):
            st.session_state["modulo_activo"] = "nyper"
            st.rerun()
    with _lc2:
        st.markdown("""
        <div style="background:#f7f9fc;border:1px solid #e0e5ec;border-radius:14px;padding:2rem 1.5rem;text-align:center;font-family:'Montserrat',sans-serif;margin-bottom:1rem">
            <div style="font-size:3rem;margin-bottom:1rem">📋</div>
            <h3 style="font-size:1.1rem;font-weight:700;color:#1a1a2e;margin:0 0 .5rem">Mi Cartera</h3>
            <p style="font-size:.85rem;color:#555;line-height:1.6;margin:0">Tu cartera personal de clientes<br>y contactos del territorio</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Mi Cartera", key="landing_cartera", use_container_width=True):
            st.session_state["modulo_activo"] = "cartera"
            st.rerun()

    st.markdown(f"""
    <div style="text-align:center;margin-top:2rem;padding:1rem 0;border-top:1px solid #e0e5ec">
        <p style="font-size:.75rem;color:#999;font-family:'Montserrat',sans-serif">NyPer v4.0 · {usuario['nombre']} {usuario['apellido']}</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Módulo Cartera ───────────────────────────────────────────────────────────
if st.session_state.get("modulo_activo") == "cartera":
    from services.db import (
        listar_cartera, guardar_cliente_cartera,
        actualizar_cliente_cartera, eliminar_cliente_cartera, importar_cartera_excel,
        importar_informe_roles, listar_usuarios, CRITERIOS_COMERCIALES,
    )

    col_hdr_c1, col_hdr_c2 = st.columns([3, 1])
    with col_hdr_c1:
        st.markdown(f"""
        <div class="hdr-mark" style="display:none"></div>
        <div class="hdr-content">
          {_NYPER_LOGO_HTML}
          <p>Mi Cartera</p>
        </div>
        """, unsafe_allow_html=True)

    _mi_email_c = usuario["email"]
    _es_admin_c = usuario.get("rol") == "admin"

    # Admin puede ver todas las carteras
    if _es_admin_c:
        _usuarios_c = listar_usuarios()
        _emails_c = [_mi_email_c] + [u["email"] for u in _usuarios_c if u["email"] != _mi_email_c and u["activo"]]
        _nombres_c = {u["email"]: f"{u['nombre']} {u['apellido']}" for u in _usuarios_c}
        _nombres_c[_mi_email_c] = f"{usuario['nombre']} {usuario['apellido']}"
        _ver_email = st.selectbox(
            "Ver cartera de",
            _emails_c,
            format_func=lambda e: f"{_nombres_c.get(e, e)} (yo)" if e == _mi_email_c else _nombres_c.get(e, e),
            key="cartera_ver_de",
        )
    else:
        _ver_email = _mi_email_c

    clientes = listar_cartera(_ver_email)

    # KPIs
    kc1, kc2, kc3 = st.columns(3)
    kc1.metric("Total clientes", len(clientes))
    _rubros_c = {}
    for c in clientes:
        r = c.get("rubro", "") or "Sin rubro"
        _rubros_c[r] = _rubros_c.get(r, 0) + 1
    _top_rubro = max(_rubros_c, key=_rubros_c.get) if _rubros_c else "—"
    kc2.metric("Rubro principal", _top_rubro)
    kc3.metric("Rubros distintos", len(_rubros_c))

    # ── Carga manual ─────────────────────────────────────────────────────────
    with st.expander("➕ Agregar cliente manual", expanded=False):
        mc1, mc2 = st.columns(2)
        with mc1:
            _c_nombre = st.text_input("Nombre / Razón Social *", key="c_nombre")
            _c_cuit = st.text_input("CUIT", key="c_cuit")
            _c_rubro = st.text_input("Rubro", key="c_rubro")
            _c_subrubro = st.text_input("Subrubro", key="c_subrubro")
            _c_telefono = st.text_input("Teléfono", key="c_telefono")
        with mc2:
            _c_mail = st.text_input("Email", key="c_mail")
            _c_dir = st.text_input("Dirección", key="c_dir")
            _c_loc = st.text_input("Localidad", key="c_loc")
            _c_obs = st.text_area("Observaciones", height=120, key="c_obs")
        if st.button("Guardar cliente", key="btn_guardar_cliente", use_container_width=True):
            if not _c_nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                guardar_cliente_cartera(_ver_email if _es_admin_c else _mi_email_c, {
                    "nombre_razon_social": _c_nombre.strip(),
                    "cuit": _c_cuit.strip(),
                    "rubro": _c_rubro.strip(),
                    "subrubro": _c_subrubro.strip(),
                    "telefono": _c_telefono.strip(),
                    "mail": _c_mail.strip(),
                    "direccion": _c_dir.strip(),
                    "localidad": _c_loc.strip(),
                    "observaciones": _c_obs.strip(),
                })
                st.success(f"Cliente '{_c_nombre.strip()}' guardado.")
                st.rerun()

    # ── Importar Informe Roles (pisa todo, muestra diff) ────────────────────
    _afiliado_usr = usuario.get("codigo_afiliado", "")
    with st.expander("📊 Importar Informe Roles", expanded=False):
        if not _afiliado_usr:
            st.warning("No tenés código de afiliado configurado. Pedile al admin que lo cargue en tu usuario.")
        else:
            st.caption(f"Afiliado: **{_afiliado_usr}** · Reemplaza toda la cartera con los datos del informe.")
        _archivo_roles = st.file_uploader("Informe Roles (.xlsb / .xlsx)", type=["xlsb", "xlsx", "xls"], key="roles_upload")
        if _archivo_roles and _afiliado_usr:
            if st.button("Importar y reemplazar", key="btn_importar_roles", use_container_width=True, type="primary"):
                _target_email = _ver_email if _es_admin_c else _mi_email_c
                _target_afiliado = _afiliado_usr
                # Si admin ve otro usuario, usar afiliado de ese usuario
                if _es_admin_c and _ver_email != _mi_email_c:
                    _u_target = [u for u in listar_usuarios() if u["email"] == _ver_email]
                    _target_afiliado = _u_target[0].get("codigo_afiliado", "") if _u_target else ""
                _diff = importar_informe_roles(_target_email, _archivo_roles, _target_afiliado)
                st.session_state["_ultimo_diff_roles"] = _diff
                st.rerun()

    # Mostrar diff si acaba de importar
    _diff_roles = st.session_state.pop("_ultimo_diff_roles", None)
    if _diff_roles:
        st.success(f"Importados {_diff_roles['importados']} clientes.")
        if _diff_roles["clientes_nuevos"]:
            st.markdown(f"**Clientes nuevos ({len(_diff_roles['clientes_nuevos'])}):** {', '.join(_diff_roles['clientes_nuevos'][:10])}")
        if _diff_roles["clientes_perdidos"]:
            st.warning(f"**Clientes que salieron ({len(_diff_roles['clientes_perdidos'])}):** {', '.join(_diff_roles['clientes_perdidos'][:10])}")
        if _diff_roles["cambios_criterios"]:
            st.markdown("**Cambios en criterios:**")
            for _cc in _diff_roles["cambios_criterios"]:
                _sub = ", ".join(CRITERIOS_COMERCIALES.get(k, k) for k in _cc["subieron"])
                _baj = ", ".join(CRITERIOS_COMERCIALES.get(k, k) for k in _cc["bajaron"])
                _linea = f"• **{_cc['nombre']}**"
                if _sub:
                    _linea += f" — subieron: {_sub}"
                if _baj:
                    _linea += f" — bajaron: {_baj}"
                st.markdown(_linea)
        elif not _diff_roles["clientes_nuevos"] and not _diff_roles["clientes_perdidos"]:
            st.info("Sin cambios respecto a la cartera anterior.")
        # Recargar clientes después de importar
        clientes = listar_cartera(_ver_email)

    # ── Importar Excel genérico (agrega) ─────────────────────────────────────
    with st.expander("📥 Agregar desde Excel", expanded=False):
        _archivo = st.file_uploader("Excel (.xlsx)", type=["xlsx", "xls"], key="cartera_upload")
        if _archivo:
            _df_imp = pd.read_excel(_archivo, dtype=str)
            st.dataframe(_df_imp.head(5), use_container_width=True)
            st.caption(f"{len(_df_imp)} filas detectadas")
            if st.button("Agregar a cartera", key="btn_importar_cartera", use_container_width=True):
                _count = importar_cartera_excel(_ver_email if _es_admin_c else _mi_email_c, _df_imp)
                st.success(f"{_count} clientes agregados.")
                st.rerun()

    # ── Tabla de clientes ────────────────────────────────────────────────────
    st.divider()
    if not clientes:
        st.info("No hay clientes en la cartera. Importá el informe roles o agregá prospectos desde Buscar Clientes.")
    else:
        import json as _json

        # Buscador
        _busq_c = st.text_input("Buscar", placeholder="Nombre, CUIT, rubro...", key="cartera_buscar", label_visibility="collapsed")
        if _busq_c:
            _qc = _busq_c.lower()
            clientes = [c for c in clientes if
                _qc in (c.get("nombre_razon_social", "") or "").lower()
                or _qc in (c.get("cuit", "") or "").lower()
                or _qc in (c.get("rubro", "") or "").lower()
                or _qc in (c.get("localidad", "") or "").lower()
            ]

        st.caption(f"{len(clientes)} clientes")

        for cli in clientes:
            # Parsear criterios
            try:
                _crits = _json.loads(cli.get("criterios_json", "{}"))
            except (_json.JSONDecodeError, TypeError):
                _crits = {}
            _cumple = sum(1 for v in _crits.values() if v)
            _total_crit = len(CRITERIOS_COMERCIALES)

            with st.container(border=True):
                cc1, cc2, cc3 = st.columns([3, 2, 1])
                with cc1:
                    _nombre_cli = cli['nombre_razon_social']
                    st.markdown(f"**{_nombre_cli}**")
                    _detalles = []
                    if cli.get("cuit"):
                        _detalles.append(f"CUIT: {cli['cuit']}")
                    if cli.get("rubro"):
                        _detalles.append(cli["rubro"])
                    if cli.get("localidad"):
                        _detalles.append(cli["localidad"])
                    st.caption(" · ".join(_detalles) if _detalles else "")
                with cc2:
                    if cli.get("telefono"):
                        st.markdown(f"📞 {cli['telefono']}")
                    if cli.get("mail"):
                        st.markdown(f"📧 {cli['mail']}")
                    if cli.get("direccion"):
                        st.caption(f"📍 {cli['direccion']}")
                with cc3:
                    # Scoring criterios
                    if _crits:
                        _color_score = "#00A651" if _cumple >= _total_crit * 0.5 else "#e53e3e"
                        st.markdown(f'<div style="text-align:center;padding:.5rem"><span style="font-size:1.5rem;font-weight:700;color:{_color_score}">{_cumple}/{_total_crit}</span><br><span style="font-size:.7rem;color:#666">criterios</span></div>', unsafe_allow_html=True)

                # Criterios como badges
                if _crits:
                    _badges = ""
                    for _ck, _cl in CRITERIOS_COMERCIALES.items():
                        if _crits.get(_ck):
                            _badges += f'<span style="background:#e8f5ee;color:#00A651;padding:2px 8px;border-radius:12px;font-size:.7rem;font-weight:600;margin:2px">{_cl}</span> '
                        else:
                            _badges += f'<span style="background:#fff0f0;color:#e53e3e;padding:2px 8px;border-radius:12px;font-size:.7rem;font-weight:600;margin:2px">{_cl}</span> '
                    st.markdown(f'<div style="margin-top:4px;line-height:2">{_badges}</div>', unsafe_allow_html=True)

            # Editar en expander
            with st.expander(f"Editar {cli['nombre_razon_social']}", expanded=False):
                ec1, ec2 = st.columns(2)
                _cid = cli["id"]
                with ec1:
                    _en = st.text_input("Nombre", value=cli["nombre_razon_social"], key=f"ce_nom_{_cid}")
                    _ec = st.text_input("CUIT", value=cli.get("cuit", ""), key=f"ce_cuit_{_cid}")
                    _er = st.text_input("Rubro", value=cli.get("rubro", ""), key=f"ce_rub_{_cid}")
                    _et = st.text_input("Teléfono", value=cli.get("telefono", ""), key=f"ce_tel_{_cid}")
                with ec2:
                    _em = st.text_input("Email", value=cli.get("mail", ""), key=f"ce_mail_{_cid}")
                    _ed = st.text_input("Dirección", value=cli.get("direccion", ""), key=f"ce_dir_{_cid}")
                    _el = st.text_input("Localidad", value=cli.get("localidad", ""), key=f"ce_loc_{_cid}")
                    _eo = st.text_area("Observaciones", value=cli.get("observaciones", ""), key=f"ce_obs_{_cid}", height=80)

                # Editar criterios manualmente
                st.markdown("**Criterios comerciales:**")
                _crit_cols = st.columns(3)
                _crit_editados = {}
                for idx, (_ck, _cl) in enumerate(CRITERIOS_COMERCIALES.items()):
                    with _crit_cols[idx % 3]:
                        _crit_editados[_ck] = st.checkbox(_cl, value=_crits.get(_ck, False), key=f"ce_crit_{_ck}_{_cid}")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Guardar cambios", key=f"ce_save_{_cid}", use_container_width=True):
                        actualizar_cliente_cartera(_cid, {
                            "nombre_razon_social": _en, "cuit": _ec, "rubro": _er,
                            "telefono": _et, "mail": _em, "direccion": _ed,
                            "localidad": _el, "observaciones": _eo,
                            "criterios_json": _json.dumps(_crit_editados, ensure_ascii=False),
                        })
                        st.success("Actualizado.")
                        st.rerun()
                with bc2:
                    if st.button("Eliminar", key=f"ce_del_{_cid}", use_container_width=True):
                        eliminar_cliente_cartera(_cid)
                        st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO NYPER — Buscar Clientes
# ══════════════════════════════════════════════════════════════════════════════

col_hdr1, col_hdr2 = st.columns([3, 2])
with col_hdr1:
    st.markdown(f"""
    <div class="hdr-mark" style="display:none"></div>
    <div class="hdr-content">
      {_NYPER_LOGO_HTML}
      <p>Inteligencia comercial para Roles NyP</p>
    </div>
    """, unsafe_allow_html=True)
with col_hdr2:
    todas_keys = list(SUCURSALES.keys())
    # Recuperar sucursal guardada en disco si es primera carga
    if "sucursal_sel" not in st.session_state:
        _cfg = _cargar_config()
        _suc_guardada = _cfg.get("sucursal_sel", SUCURSAL_DEFAULT)
        if _suc_guardada in todas_keys:
            st.session_state["sucursal_sel"] = _suc_guardada
        else:
            st.session_state["sucursal_sel"] = SUCURSAL_DEFAULT

    def _seleccionar_suc(opcion):
        _guardar_config({"sucursal_sel": opcion})
        st.session_state["sucursal_sel"] = opcion
        st.session_state["suc_search"] = ""

    busq_suc = st.text_input(
        "suc_input",
        placeholder="Código o nombre de sucursal...",
        label_visibility="collapsed",
        key="suc_search",
    )
    _q = busq_suc.strip().lower() if busq_suc else ""
    if _q:
        coincidencias = [k for k in todas_keys if _q in k.lower()]
        for i, opcion in enumerate(coincidencias[:8]):
            st.button(opcion, key=f"suc_btn_{i}", use_container_width=True,
                      on_click=_seleccionar_suc, args=(opcion,))
        if not coincidencias:
            st.caption("Sin coincidencias")
    else:
        st.caption(f"📍 {st.session_state['sucursal_sel']}")

SUC = SUCURSALES[st.session_state["sucursal_sel"]]
SUCURSAL_LAT = SUC["lat"]
SUCURSAL_LNG = SUC["lng"]
SUCURSAL_DIR = SUC["dir"]
SUCURSAL_CODIGO = st.session_state["sucursal_sel"].split(" — ")[0]
RADIO_KM = 2

# Nombre del operador — viene del sistema de auth
st.session_state["nombre_usuario"] = f"{usuario['nombre']} {usuario['apellido']}"

st.caption(f"📍 {SUCURSAL_DIR} · {SUC.get('partido', '')} ({SUCURSAL_LAT:.4f}, {SUCURSAL_LNG:.4f}) · 👤 {st.session_state['nombre_usuario']}")


# ── Helpers de persistencia ───────────────────────────────────────────────────

def cargar_leads(codigo_suc=None):
    key = f"leads_{codigo_suc}" if codigo_suc else "leads"
    return storage_get(key, [])


def guardar_leads(leads, codigo_suc=None):
    key = f"leads_{codigo_suc}" if codigo_suc else "leads"
    storage_set(key, leads)


def guardar_historial(leads):
    os.makedirs(HISTORIAL_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    with open(f"{HISTORIAL_DIR}/{ts}.json", "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def _score_contacto(lead):
    """Puntaje de completitud de contacto — reemplaza sistema A/B/C/D."""
    score = 0
    if lead.get("phone_norm"): score += 3
    if lead.get("whatsapp_probable"): score += 3
    if lead.get("email_primary"): score += 2
    if lead.get("website"): score += 1
    if lead.get("instagram_url") or lead.get("facebook_url"): score += 1
    score += (lead.get("rating", 0) or 0) / 10
    return score


def migrar_si_necesario(leads):
    """Migra leads al nuevo modelo si vienen del formato viejo."""
    if not leads:
        return leads
    from services.normalizer import migrar_batch
    from services.channel_classifier import clasificar_batch

    if "lead_id" not in leads[0]:
        leads = migrar_batch(leads, SUCURSAL_LAT, SUCURSAL_LNG)
        clasificar_batch(leads)
        leads.sort(key=_score_contacto, reverse=True)
        guardar_leads(leads, SUCURSAL_CODIGO)
    return leads


# ── Cargar datos por sucursal (cada sucursal tiene sus propios leads) ─────────

# Detectar cambio de sucursal → guardar leads actuales y cargar los de la nueva
if "sucursal_activa" not in st.session_state:
    st.session_state["sucursal_activa"] = SUCURSAL_CODIGO

if st.session_state["sucursal_activa"] != SUCURSAL_CODIGO:
    # Guardar leads de la sucursal anterior antes de cambiar
    if st.session_state.get("leads"):
        guardar_leads(st.session_state["leads"], st.session_state["sucursal_activa"])
    # Cargar leads de la nueva sucursal
    st.session_state["sucursal_activa"] = SUCURSAL_CODIGO
    leads_disco = cargar_leads(SUCURSAL_CODIGO)
    st.session_state["leads"] = migrar_si_necesario(leads_disco)

elif "leads" not in st.session_state:
    leads_disco = cargar_leads(SUCURSAL_CODIGO)
    st.session_state["leads"] = migrar_si_necesario(leads_disco)


# ── Tabs principales ──────────────────────────────────────────────────────────

(tab_inicio, tab_descubrir, tab_enriquecer, tab_bandeja,
 tab_exportar, tab_prospectos, tab_analisis) = st.tabs([
    "🏠 Inicio",
    "🔍 Descubrir",
    "⚡ Enriquecer",
    "📋 Bandeja",
    "📤 Exportar",
    "⭐ Prospectos",
    "📊 Análisis",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0: INICIO
# ══════════════════════════════════════════════════════════════════════════════

with tab_inicio:
    _logo_b64 = img_to_base64("assets/logo_bp.jpg")
    _logo_img = f'<img src="data:image/jpeg;base64,{_logo_b64}" class="logo-bp" alt="Banco Provincia">' if _logo_b64 else '<div style="font-family:Montserrat,sans-serif;font-size:1.5rem;font-weight:700;color:#00A651;margin-bottom:1rem">Banco Provincia</div>'

    # Hero
    _nyper_hero = f'<img src="data:image/png;base64,{_NYPER_LOGO_B64}" class="hero-nyper-logo" alt="NyPer">' if _NYPER_LOGO_B64 else '<h1 style="font-size:3.5rem;font-weight:900;color:#00A651;margin:0">NyPer</h1>'

    _perrito_nyp_hero = f'<img src="data:image/png;base64,{_PERRITO_NYP_B64}" class="hero-perrito" alt="NyPer mascota">' if _PERRITO_NYP_B64 else ''

    st.markdown(f"""
    <div class="home-hero">
        <div class="home-logos-row">
            {_logo_img}
            {_perrito_nyp_hero}
            {_nyper_hero}
        </div>
        <div class="subtitle">Inteligencia Comercial Territorial</div>
        <p class="hero-desc">
            Herramienta de apoyo para los Roles NyP orientada a transformar el territorio
            de cada sucursal en oportunidades comerciales accionables.
        </p>
        <div class="home-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    # Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="home-card">
            <div class="card-icon" style="display:flex;justify-content:center"><svg width="40" height="40" viewBox="0 0 24 24" fill="none"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="#EA4335"/><circle cx="12" cy="9" r="2.5" fill="#fff"/></svg></div>
            <h3>Descubrir</h3>
            <p>Identifica comercios, pymes y profesionales dentro del área de influencia de cada sucursal.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="home-card">
            <div class="card-icon" style="display:flex;justify-content:center"><svg width="40" height="40" viewBox="0 0 24 24" fill="none"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="#4285F4"/><path d="M20 9v-3h-2v3h-3v2h3v3h2v-3h3v-2h-3z" fill="#00A651"/></svg></div>
            <h3>Enriquecer</h3>
            <p>Consolida información pública relevante para facilitar una gestión comercial más ágil.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="home-card">
            <div class="card-icon" style="display:flex;justify-content:center"><svg width="40" height="40" viewBox="0 0 24 24" fill="none"><path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z" fill="#00A651"/></svg></div>
            <h3>Priorizar</h3>
            <p>Organiza oportunidades según su contactabilidad real y su posibilidad de acción comercial inmediata.</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="home-card">
            <div class="card-icon" style="display:flex;justify-content:center"><svg width="40" height="40" viewBox="0 0 24 24" fill="none"><path d="M19 9h-4V3H9v6H5l7 7 7-7z" fill="#00A651"/><path d="M5 18v2h14v-2H5z" fill="#00B8D4"/></svg></div>
            <h3>Exportar</h3>
            <p>Genera listados listos para campañas, seguimiento y gestión territorial.</p>
        </div>
        """, unsafe_allow_html=True)

    # Seccion: Apoyo a Roles NyP
    st.markdown("""
    <div class="home-section">
        <div class="section-label">Apoyo a Roles NyP</div>
        <h3>Detectar, calificar y accionar — desde la sucursal</h3>
        <p>
            NyPer le da al Rol NyP una base de prospectos territorial, enriquecida y lista
            para trabajar. Permite elegir qué rubros buscar, ordenar por cantidad de reseñas,
            buscar CUIT en ARCA cuando se trata de personas jurídicas y consultar situación
            BCRA de forma masiva a través de la API. Le suma teléfono, email y redes sociales,
            y clasifica cada lead por canal de contacto y prioridad. El resultado es un listado
            accionable: sabés a quién contactar, por dónde y por qué.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Seccion: Fuentes publicas
    st.markdown("""
    <div class="home-section">
        <div class="section-label">Opera con fuentes públicas</div>
        <h3>Opera exclusivamente con fuentes públicas</h3>
        <p>
            NyPer no consulta bases internas de clientes, no requiere integración con sistemas
            core y no trabaja con información confidencial del banco. Consolida información
            de acceso público para uso comercial territorial.
        </p>
        <div class="home-sources">
            <span>Google Places API</span>
            <span>ARCA / AFIP</span>
            <span>BCRA</span>
            <span>Sitios web públicos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Flujo visual
    st.markdown("""
    <div class="home-flow">
        <div class="flow-label">Flujo de trabajo</div>
        <p class="flow-steps">
            <span class="step">Seleccionar sucursal</span>
            <span class="arrow">→</span>
            <span class="step">Descubrir oportunidades</span>
            <span class="arrow">→</span>
            <span class="step">Enriquecer información</span>
            <span class="arrow">→</span>
            <span class="step">Revisar bandeja</span>
            <span class="arrow">→</span>
            <span class="step">Exportar y accionar</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Panel de administración (solo admin) ─────────────────────────────────
    if es_admin():
        st.divider()
        with st.expander("🔧 Administración", expanded=False):
            admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Usuarios", "Reasignar gestores", "Configuración"])

            with admin_tab1:
                # Crear usuario
                st.markdown("##### Crear usuario")
                ac1, ac2 = st.columns(2)
                with ac1:
                    nuevo_nombre = st.text_input("Nombre", key="admin_nombre")
                    nuevo_email = st.text_input("Email @bpba.com.ar", key="admin_email")
                    nuevo_rol = st.selectbox("Rol", ["usuario", "admin"], key="admin_rol")
                with ac2:
                    nuevo_apellido = st.text_input("Apellido", key="admin_apellido")
                    nuevo_pw = st.text_input("Contraseña", type="password", key="admin_pw")
                    nuevo_color = st.color_picker("Color", "#3b82f6", key="admin_color")
                    nuevo_afiliado = st.text_input("Código afiliado (ej: P047071)", key="admin_afiliado")
                if st.button("Crear usuario", key="btn_crear_usr"):
                    from services.auth import validar_dominio
                    from services.db import crear_usuario, actualizar_usuario as _upd_usr
                    if not nuevo_nombre or not nuevo_apellido or not nuevo_email or not nuevo_pw:
                        st.error("Completá todos los campos.")
                    elif not validar_dominio(nuevo_email):
                        st.error("Solo emails @bpba.com.ar")
                    else:
                        ok = crear_usuario(nuevo_email.strip().lower(), nuevo_nombre.strip(), nuevo_apellido.strip(), nuevo_pw, nuevo_rol, nuevo_color)
                        if ok and nuevo_afiliado.strip():
                            _upd_usr(nuevo_email.strip().lower(), codigo_afiliado=nuevo_afiliado.strip().upper())
                        if ok:
                            st.success(f"Usuario {nuevo_email} creado.")
                        else:
                            st.error("Ya existe un usuario con ese email.")

                # Listar usuarios
                st.markdown("##### Usuarios registrados")
                from services.db import listar_usuarios, actualizar_usuario
                usuarios_lista = listar_usuarios()
                for u in usuarios_lista:
                    uc1, uc2, uc3 = st.columns([3, 1, 1])
                    with uc1:
                        _color_dot = f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{u["color"]};margin-right:6px"></span>'
                        _afil = f' · Afiliado: {u.get("codigo_afiliado", "")}' if u.get("codigo_afiliado") else ""
                        st.markdown(f'{_color_dot} **{u["nombre"]} {u["apellido"]}** · {u["email"]} · {u["rol"]}{_afil}', unsafe_allow_html=True)
                    with uc2:
                        _estado_txt = "Activo" if u["activo"] else "Inactivo"
                        st.caption(_estado_txt)
                    with uc3:
                        if u["email"] != usuario["email"]:
                            _label = "Desactivar" if u["activo"] else "Activar"
                            if st.button(_label, key=f"toggle_{u['email']}"):
                                actualizar_usuario(u["email"], activo=0 if u["activo"] else 1)
                                st.rerun()

            with admin_tab2:
                st.markdown("##### Reasignar gestores")
                leads_all = st.session_state.get("leads", [])
                prospectos_con_owner = [l for l in leads_all if l.get("en_prospectos") and l.get("owner_email")]
                if not prospectos_con_owner:
                    st.info("No hay prospectos asignados.")
                else:
                    from services.db import listar_usuarios, reasignar_ownership
                    _usuarios_db = listar_usuarios()
                    _emails_activos = [u["email"] for u in _usuarios_db if u["activo"]]
                    _nombres_map = {u["email"]: f"{u['nombre']} {u['apellido']}" for u in _usuarios_db}
                    _colores_map = {u["email"]: u["color"] for u in _usuarios_db}
                    for lp in prospectos_con_owner:
                        _lk = lp.get("lead_id", "")
                        rc1, rc2, rc3 = st.columns([3, 2, 1])
                        with rc1:
                            st.markdown(f"**{lp.get('business_name_raw', '—')}**")
                            st.caption(f"Gestor actual: {lp.get('owner_nombre', '')}")
                        with rc2:
                            nuevo_owner = st.selectbox(
                                "Nuevo gestor", _emails_activos,
                                format_func=lambda e: _nombres_map.get(e, e),
                                key=f"reasig_{_lk}",
                            )
                        with rc3:
                            if st.button("Reasignar", key=f"btn_reasig_{_lk}"):
                                reasignar_ownership(_lk, SUCURSAL_CODIGO, nuevo_owner)
                                lp["owner_email"] = nuevo_owner
                                lp["owner_nombre"] = _nombres_map.get(nuevo_owner, nuevo_owner)
                                lp["owner_color"] = _colores_map.get(nuevo_owner, "#3b82f6")
                                guardar_leads(leads_all, SUCURSAL_CODIGO)
                                st.session_state["leads"] = leads_all
                                st.rerun()

            with admin_tab3:
                st.markdown("##### Configuración general")
                _cfg_actual = _cargar_config()
                _max_pr = _cfg_actual.get("max_prospectos_por_usuario", 30)
                _nuevo_max = st.number_input("Máx. prospectos por usuario", min_value=5, max_value=200, value=_max_pr, step=5, key="admin_max_pr")
                if _nuevo_max != _max_pr:
                    _guardar_config({"max_prospectos_por_usuario": _nuevo_max})
                    st.success(f"Límite actualizado a {_nuevo_max} prospectos por usuario.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: DESCUBRIR
# ══════════════════════════════════════════════════════════════════════════════

with tab_descubrir:
    st.markdown("### Descubrir leads territoriales")

    leads_actuales = st.session_state.get("leads", [])
    if leads_actuales:
        c1, c2, c3 = st.columns(3)
        c1.metric("Leads en base", len(leads_actuales))
        c2.metric("Con contacto", sum(1 for l in leads_actuales if l.get("contact_available")))
        c3.metric("Con WhatsApp", sum(1 for l in leads_actuales if l.get("whatsapp_probable")))
        st.info(f"Base con {len(leads_actuales)} leads. Podés buscar nuevos o trabajar con los existentes.")
        st.divider()

    # Rubros disponibles para filtrar
    RUBROS_DISPONIBLES = {
        "Gastronomía": ["restaurant", "bakery", "cafe", "meal_delivery", "meal_takeaway", "bar", "night_club"],
        "Comercio": ["store", "supermarket", "clothing_store", "shoe_store", "furniture_store",
                     "home_goods_store", "jewelry_store", "book_store", "pet_store", "florist",
                     "laundry", "car_wash", "locksmith"],
        "Salud": ["pharmacy", "dentist", "doctor", "veterinary_care", "hospital", "physiotherapist"],
        "Educación": ["school", "university", "library"],
        "Servicios profesionales": ["lawyer", "accounting", "real_estate_agency", "travel_agency",
                                    "insurance_agency", "spa", "beauty_salon", "taxi_stand"],
        "Automotor": ["car_repair", "car_dealer", "gas_station"],
        "Construcción": ["hardware_store", "general_contractor", "plumber", "electrician",
                         "painter", "roofing_contractor"],
        "Gimnasio y bienestar": ["gym"],
        "Tecnología": ["electronics_store"],
        "Logística": ["moving_company", "storage"],
        "Alojamiento y turismo": ["lodging", "shopping_mall", "campground"],
        "Entretenimiento": ["movie_theater", "amusement_park", "bowling_alley", "museum"],
        "Otros servicios": ["parking", "funeral_home", "transit_station"],
    }

    col_a, col_b = st.columns(2)
    with col_a:
        radio = st.slider("Radio de búsqueda (km)", 1, 3, min(int(RADIO_KM), 3))
        min_reseñas = st.slider("Mínimo de reseñas", 0, 50, 5)
    with col_b:
        st.caption(f"Centro: {SUCURSAL_DIR}")

    rubros_sel = st.multiselect(
        "Rubros a buscar *",
        list(RUBROS_DISPONIBLES.keys()),
        default=[],
        key="rubros_busqueda",
        placeholder="Elegí al menos un rubro",
    )

    if not rubros_sel:
        st.warning("Seleccioná al menos un rubro para buscar.")

    st.divider()

    if st.button("🔍 Buscar y enriquecer comercios", width="stretch", disabled=not rubros_sel):
        from services.prospector import buscar_comercios
        from utils.geo import zona_desde_direccion
        from services.normalizer import migrar_batch
        from services.channel_classifier import clasificar_batch
        from services.contact_enricher import enriquecer_contacto
        # from services.cuentadni_scraper import cruzar_leads_con_cuentadni
        from services.deduper import detectar_duplicados

        if leads_actuales:
            guardar_historial(leads_actuales)

        # Armar lista de types de Google Places según rubros seleccionados
        types_buscar = []
        for rubro_nombre in rubros_sel:
            types_buscar.extend(RUBROS_DISPONIBLES.get(rubro_nombre, []))
        types_buscar = list(set(types_buscar))

        # ── Paso 1: Descubrir ────────────────────────────────────────────────
        perrito_placeholder = st.empty()
        if _PERRITO_HTML:
            perrito_placeholder.markdown(f"""
            <div class="perrito-buscando">
                {_PERRITO_HTML}
                <p>Olfateando oportunidades en la zona...</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            perrito_placeholder.info("Buscando en Google Places...")

        nuevos = buscar_comercios(SUCURSAL_LAT, SUCURSAL_LNG, radio, min_reseñas=min_reseñas, rubros_filtro=types_buscar)
        for c in nuevos:
            c["zona"] = zona_desde_direccion(c.get("direccion", ""), c["lat"], c["lng"])

        perrito_placeholder.empty()
        st.success(f"✅ {len(nuevos)} comercios encontrados")
        nuevos = migrar_batch(nuevos, SUCURSAL_LAT, SUCURSAL_LNG)
        clasificar_batch(nuevos)

        # Cruce Cuenta DNI — desactivado temporalmente
        # _total_cdni, _matches_cdni = cruzar_leads_con_cuentadni(nuevos)
        # if _matches_cdni:
        #     st.info(f"💳 {_matches_cdni} comercios ya tienen Cuenta DNI")

        # Merge con base existente
        existentes_por_id = {l.get("source_place_id", ""): l for l in leads_actuales if l.get("source_place_id")}
        actualizados = 0
        agregados = 0
        for nuevo in nuevos:
            pid = nuevo.get("source_place_id", "")
            if pid and pid in existentes_por_id:
                viejo = existentes_por_id[pid]
                for k, v in nuevo.items():
                    if v:
                        viejo[k] = v
                actualizados += 1
            else:
                leads_actuales.append(nuevo)
                if pid:
                    existentes_por_id[pid] = nuevo
                agregados += 1
        st.info(f"➕ {agregados} nuevos · 🔄 {actualizados} actualizados")
        st.session_state["leads"] = leads_actuales
        guardar_leads(leads_actuales, SUCURSAL_CODIGO)

        # ── Paso 2: Enriquecer contacto (solo los nuevos sin telefono) ───────
        candidatos = [l for l in leads_actuales if not l.get("phone_norm")]
        total_c = len(candidatos)
        if total_c > 0:
            col_prog, col_perro = st.columns([3, 1])
            with col_prog:
                barra = st.progress(0)
                estado = st.empty()
                estado.info(f"Enriqueciendo contacto: 0/{total_c}")
            with col_perro:
                perrito_ph = st.empty()
                if _PERRITO_HTML:
                    perrito_ph.markdown(f"""
                    <div class="perrito-buscando">
                        {_PERRITO_HTML}
                        <p>Olfateando datos de contacto...</p>
                    </div>
                    """, unsafe_allow_html=True)

            for idx, lead in enumerate(candidatos):
                enriquecer_contacto(lead)
                progreso = (idx + 1) / total_c
                barra.progress(min(progreso, 1.0))
                estado.info(f"Enriqueciendo contacto: {idx + 1}/{total_c} ({progreso:.0%})")
                if (idx + 1) % 50 == 0:
                    guardar_leads(leads_actuales, SUCURSAL_CODIGO)

            barra.empty()
            estado.empty()
            perrito_ph.empty()

        # ── Paso 3: Clasificar, dedup, guardar ───────────────────────────────
        clasificar_batch(leads_actuales)
        leads_actuales, _, _ = detectar_duplicados(leads_actuales)
        leads_actuales.sort(key=_score_contacto, reverse=True)
        guardar_leads(leads_actuales, SUCURSAL_CODIGO)
        st.session_state["leads"] = leads_actuales

        # Resultado final
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(leads_actuales))
        c2.metric("Contactables", sum(1 for l in leads_actuales if l.get("contact_available")))
        c3.metric("Con WhatsApp", sum(1 for l in leads_actuales if l.get("whatsapp_probable")))
        c4.metric("Con email", sum(1 for l in leads_actuales if l.get("email_primary")))
        st.success("Listo. Revisá los resultados en **Bandeja**.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: ENRIQUECER
# ══════════════════════════════════════════════════════════════════════════════

with tab_enriquecer:
    st.markdown("### Enriquecimiento profundo")
    st.caption("El enriquecimiento de contacto básico (teléfono, email, redes) ya se ejecuta automáticamente al buscar comercios.")
    leads = st.session_state.get("leads", [])

    if not leads:
        st.warning("No hay leads. Primero buscá comercios en **Descubrir**.")
    else:
        sin_tel = sum(1 for l in leads if not l.get("phone_norm"))
        contactables = sum(1 for l in leads if l.get("contact_available"))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Contactables", contactables)
        c2.metric("Sin teléfono", sin_tel)
        c3.metric("Sin email", sum(1 for l in leads if not l.get("email_primary")))
        c4.metric("Sin redes", sum(1 for l in leads if not l.get("instagram_url") and not l.get("facebook_url")))

        st.divider()

        # ── Rastreo profundo de websites
        st.markdown("#### 1. Rastrear websites")
        con_web = sum(1 for l in leads if l.get("website"))
        ya_rastreados = sum(1 for l in leads if l.get("website_rastreado"))
        pendientes_web = con_web - ya_rastreados
        st.caption(f"Leads con website: {con_web} — Ya rastreados: {ya_rastreados} — Pendientes: {pendientes_web}")

        if st.button("🌐 Rastrear websites", width="stretch"):
            from services.contact_enricher import rastrear_websites_batch
            from services.channel_classifier import clasificar_batch as clas_batch2

            col_pw, col_prw = st.columns([3, 1])
            with col_pw:
                barra_w = st.progress(0)
                estado_w = st.empty()
                estado_w.info(f"Rastreando websites: 0/{pendientes_web}")
            with col_prw:
                perrito_w = st.empty()
                if _PERRITO_HTML:
                    perrito_w.markdown(f"""
                    <div class="perrito-buscando">
                        {_PERRITO_HTML}
                        <p>Rastreando websites...</p>
                    </div>
                    """, unsafe_allow_html=True)

            def prog_web(a, t):
                barra_w.progress(min(a / t, 1.0) if t > 0 else 1.0)
                estado_w.info(f"Rastreando websites: {a}/{t} ({a/t:.0%})" if t > 0 else "Listo")

            leads, total_rastreados = rastrear_websites_batch(leads, callback=prog_web)
            barra_w.empty()
            estado_w.empty()
            perrito_w.empty()
            clas_batch2(leads)
            leads.sort(key=_score_contacto, reverse=True)
            guardar_leads(leads, SUCURSAL_CODIGO)
            st.session_state["leads"] = leads
            nuevos_email = sum(1 for l in leads if l.get("email_primary"))
            st.success(f"✅ {total_rastreados} websites rastreados — Leads con email: {nuevos_email}")

        st.divider()

        # ── Enriquecimiento profundo (CUIT / ARCA / BCRA)
        st.markdown("#### 2. CUIT / ARCA / BCRA (opcional)")
        con_cuit = sum(1 for l in leads if l.get("cuit_estado") == "resuelto")
        st.caption(f"Leads con CUIT: {con_cuit} / {len(leads)}")

        col_d1, col_d2, col_d3, col_d4 = st.columns(4)

        with col_d1:
            if st.button("🔍 Resolver CUITs", width="stretch"):
                from services.deep_enrichment import resolver_cuits
                from services.licitarg_enricher import enriquecer_licitarg_batch
                barra = st.progress(0)
                def prog_cuit(a, t):
                    barra.progress(min(a/t, 1.0), text=f"CUITs: {a}/{t}")
                with st.spinner("Cruzando con Registro de Sociedades..."):
                    leads, resueltos = resolver_cuits(leads, callback=prog_cuit)
                # Enriquecimiento LICITARG automático después de resolver CUITs (es local, instantáneo)
                leads, prov_estado = enriquecer_licitarg_batch(leads)
                barra.empty()
                guardar_leads(leads, SUCURSAL_CODIGO)
                st.session_state["leads"] = leads
                msg = f"✅ {resueltos} CUITs resueltos"
                if prov_estado:
                    msg += f" · {prov_estado} proveedores del estado detectados"
                st.success(msg)

        with col_d4:
            con_licitarg = sum(1 for l in leads if l.get("es_proveedor_estado"))
            if st.button(f"📋 Estado ({con_licitarg})", width="stretch", help="Cruzar con base de proveedores del estado (LICITARG)"):
                from services.licitarg_enricher import enriquecer_licitarg_batch
                with st.spinner("Cruzando con base LICITARG..."):
                    leads, matches = enriquecer_licitarg_batch(leads)
                guardar_leads(leads, SUCURSAL_CODIGO)
                st.session_state["leads"] = leads
                st.success(f"✅ {matches} proveedores del estado encontrados")

        with col_d2:
            if st.button("🏛 Consultar ARCA", width="stretch"):
                from services.deep_enrichment import enriquecer_arca_subset
                barra = st.progress(0)
                def prog_arca(a, t):
                    barra.progress(min(a/t, 1.0), text=f"ARCA: {a}/{t}")
                leads, ok = enriquecer_arca_subset(leads, callback=prog_arca)
                barra.empty()
                guardar_leads(leads, SUCURSAL_CODIGO)
                st.session_state["leads"] = leads
                st.success(f"✅ ARCA: {ok} consultados")

        with col_d3:
            if st.button("🏦 Consultar BCRA", width="stretch"):
                from services.deep_enrichment import enriquecer_bcra_subset, aplicar_semaforo
                barra = st.progress(0)
                def prog_bcra(a, t):
                    barra.progress(min(a/t, 1.0), text=f"BCRA: {a}/{t}")
                st.info("Consulta Base deudores y Cheques rechazados")
                leads, ok = enriquecer_bcra_subset(leads, callback=prog_bcra)
                aplicar_semaforo(leads)
                barra.empty()
                guardar_leads(leads, SUCURSAL_CODIGO)
                st.session_state["leads"] = leads
                st.success(f"✅ BCRA: {ok} consultados")



# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: BANDEJA OPERATIVA
# ══════════════════════════════════════════════════════════════════════════════

with tab_bandeja:
    st.markdown("### Bandeja operativa")
    leads = st.session_state.get("leads", [])

    if not leads:
        st.warning("No hay leads. Usá **Descubrir** primero.")
    else:
        # Key dinámica: hash de sucursal + zonas reales para forzar reset al cambiar datos
        _zonas_hash = hash(frozenset(l.get("zona", "") for l in leads))
        _fk = f"{SUCURSAL_CODIGO}_{_zonas_hash}"

        with st.expander("🔽 Filtros", expanded=False):
            fc1, fc2 = st.columns(2)
            with fc1:
                canales_disp = sorted(set(l.get("primary_channel", "") for l in leads if l.get("primary_channel")))
                f_canal = st.multiselect("Canal", canales_disp, default=[], key=f"f_canal_{_fk}")
            with fc2:
                rubros_disp = sorted(set(l.get("rubro_operativo", "Otro") for l in leads))
                f_rubro = st.multiselect("Rubro", rubros_disp, default=[], key=f"f_rubro_{_fk}")

            fc5, fc6, fc7, fc8 = st.columns(4)
            with fc5:
                zonas_disp = sorted(set(l.get("zona", "") for l in leads if l.get("zona")))
                f_zona = st.multiselect("Zona", zonas_disp, default=[], placeholder="Todas las zonas", key=f"f_zona_{_fk}")
            with fc6:
                f_contactable = st.selectbox("Contactable", ["Todos", "Sí", "No"], key=f"f_cont_{_fk}")
            with fc7:
                f_vigente = st.selectbox("Vigente", ["Todos", "Sí", "No"], key=f"f_vig_{_fk}")
            with fc8:
                f_dup = st.selectbox("Duplicados", ["Mostrar todos", "Ocultar duplicados", "Solo duplicados"], key=f"f_dup_{_fk}")

            fc9, _fc10 = st.columns(2)
            with fc9:
                f_dueno = st.selectbox("Gestor", ["Todos", "Mis leads", "Sin asignar"], key=f"f_dueno_{_fk}")

        # Aplicar filtros
        filtrados = leads[:]
        if f_canal:
            filtrados = [l for l in filtrados if l.get("primary_channel") in f_canal]
        if f_rubro:
            filtrados = [l for l in filtrados if l.get("rubro_operativo", "Otro") in f_rubro]
        if f_zona:
            filtrados = [l for l in filtrados if l.get("zona", "") in f_zona]
        if f_contactable == "Sí":
            filtrados = [l for l in filtrados if l.get("contact_available")]
        elif f_contactable == "No":
            filtrados = [l for l in filtrados if not l.get("contact_available")]
        if f_vigente == "Sí":
            filtrados = [l for l in filtrados if l.get("vigencia_digital") == "vigente"]
        elif f_vigente == "No":
            filtrados = [l for l in filtrados if l.get("vigencia_digital") != "vigente"]
        if f_dup == "Ocultar duplicados":
            filtrados = [l for l in filtrados if not l.get("duplicate_flag") or l.get("master_record_flag")]
        elif f_dup == "Solo duplicados":
            filtrados = [l for l in filtrados if l.get("duplicate_flag")]
        if f_dueno == "Mis leads":
            filtrados = [l for l in filtrados if l.get("owner_email") == usuario["email"]]
        elif f_dueno == "Sin asignar":
            filtrados = [l for l in filtrados if not l.get("owner_email")]

        # Mapa (arriba, protagonista)
        try:
            import folium
            from streamlit_folium import st_folium

            mapa = folium.Map(location=[SUCURSAL_LAT, SUCURSAL_LNG], zoom_start=15, tiles="CartoDB positron")
            folium.Marker([SUCURSAL_LAT, SUCURSAL_LNG], popup=st.session_state.get("sucursal_sel", "Sucursal"),
                          icon=folium.Icon(color="blue", icon="star")).add_to(mapa)
            folium.Circle([SUCURSAL_LAT, SUCURSAL_LNG], radius=RADIO_KM * 1000,
                          color="#00A651", fill=False, opacity=0.3).add_to(mapa)
            # Color por canal de contacto
            colores_canal = {
                "whatsapp": "#25D366",
                "llamada": "#3b82f6",
                "mail": "#f97316",
                "redes": "#a855f7",
                "visita": "#6b7280",
                "sin_canal": "#9ca3af",
            }
            for l in filtrados[:500]:
                canal = l.get("primary_channel", "sin_canal")
                color = colores_canal.get(canal, "#9ca3af")
                nombre = l.get("business_name_raw", "")
                tel = l.get("phone_raw", "")
                email = l.get("email_primary", "")
                rubro = l.get("rubro_operativo", "")
                popup_html = f"<b>{nombre}</b><br>{rubro}<br>{canal}"
                if tel:
                    popup_html += f"<br>📞 {tel}"
                if email:
                    popup_html += f"<br>✉️ {email}"
                folium.CircleMarker(
                    [l["lat"], l["lng"]], radius=7,
                    color=color, fill=True, fill_color=color, fill_opacity=0.85,
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"{nombre} · {canal}",
                ).add_to(mapa)
            st_folium(mapa, width=None, height=500)
            st.caption("🟢 WhatsApp · 🔵 Llamada · 🟠 Mail/Redes · ⚫ Sin canal  (máx 500 pines)")
        except Exception as e:
            st.error(f"Error cargando mapa: {e}")

        # KPIs
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Mostrando", len(filtrados))
        c2.metric("Contactables", sum(1 for l in filtrados if l.get("contact_available")))
        c3.metric("WhatsApp", sum(1 for l in filtrados if l.get("whatsapp_probable")))
        c4.metric("Con email", sum(1 for l in filtrados if l.get("email_primary")))
        c5.metric("Para visita", sum(1 for l in filtrados if l.get("requires_visit")))
        c6.metric("Prospectos", sum(1 for l in filtrados if l.get("en_prospectos")))

        # Tabla
        CANAL_EMOJI = {"whatsapp": "💬", "llamada": "📞", "mail": "✉️", "redes": "📱", "visita": "🚶", "sin_canal": "❓"}

        if filtrados:
            def _estado_lead(l):
                if not l.get("en_prospectos"):
                    return ""
                if l.get("owner_email") == usuario["email"]:
                    return "📌 Mío"
                if l.get("owner_email"):
                    return f"🔒 {l.get('owner_nombre', '')}"
                return "⭐ Prospecto"

            df_bandeja = pd.DataFrame([{
                "Estado": _estado_lead(l),
                "Nombre": l.get("business_name_raw", ""),
                "Rubro": l.get("rubro_operativo", ""),
                "Zona": l.get("zona", ""),
                "Canal": f"{CANAL_EMOJI.get(l.get('primary_channel',''), '')} {l.get('primary_channel','')}",
                "Teléfono": l.get("phone_raw", ""),
                "Email": l.get("email_primary", ""),
                "Web": "✅" if l.get("website") else "",
                "IG": "✅" if l.get("instagram_url") else "",
                "Rating": l.get("rating", ""),
            } for l in filtrados])

            sel = st.dataframe(
                df_bandeja,
                width="stretch",
                hide_index=True,
                selection_mode="multi-row",
                on_select="rerun",
                key=f"tabla_bandeja_{_fk}",
            )
            indices_sel = sel.selection.rows if sel and hasattr(sel, "selection") else []
            leads_sel = [filtrados[i] for i in indices_sel if i < len(filtrados)]

        if leads_sel:
            # Separar libres de tomados por otro
            _libres = [l for l in leads_sel if not l.get("en_prospectos")]
            _ya_mios = [l for l in leads_sel if l.get("en_prospectos") and l.get("owner_email") == usuario["email"]]
            _tomados = [l for l in leads_sel if l.get("en_prospectos") and l.get("owner_email") and l.get("owner_email") != usuario["email"]]

            if _tomados:
                _nombres_tomados = ", ".join(l.get("business_name_raw", "?") for l in _tomados[:5])
                st.warning(f"🔒 {len(_tomados)} lead(s) ya tomados por otro gestor: {_nombres_tomados}")
            if _ya_mios:
                st.info(f"📌 {len(_ya_mios)} lead(s) ya están en tus prospectos.")

            # Límite de prospectos por usuario
            _max_prospectos = _cargar_config().get("max_prospectos_por_usuario", 30)
            _mis_prospectos_actual = sum(1 for l in leads if l.get("en_prospectos") and l.get("owner_email") == usuario["email"])
            _disponibles = max(0, _max_prospectos - _mis_prospectos_actual)

            if _libres and _disponibles == 0:
                st.error(f"Alcanzaste el límite de {_max_prospectos} prospectos. Liberá algunos antes de agregar nuevos.")
                _libres = []
            elif _libres and len(_libres) > _disponibles:
                st.warning(f"Solo podés agregar {_disponibles} más (límite: {_max_prospectos}). Se tomarán los primeros {_disponibles}.")
                _libres = _libres[:_disponibles]

            if _libres:
                if st.button(f"🎯 Agregar {len(_libres)} lead(s) a Prospectos", type="primary"):
                    from services.db import registrar_ownership
                    ahora = datetime.now().isoformat()
                    for lead in _libres:
                        lead["en_prospectos"] = True
                        lead["prospecto_estado"] = "por_contactar"
                        lead["prospecto_fecha"] = ahora
                        lead["prospecto_notas"] = ""
                        # Asignar ownership inmediatamente
                        lead["owner_email"] = usuario["email"]
                        lead["owner_nombre"] = f"{usuario['nombre']} {usuario['apellido']}"
                        lead["owner_color"] = usuario.get("color", "#3b82f6")
                        lead_key = lead.get("lead_id", "")
                        if lead_key:
                            registrar_ownership(lead_key, SUCURSAL_CODIGO, usuario["email"])
                        place_id = lead.get("source_place_id", "")
                        if place_id and not lead.get("google_photo_url"):
                            try:
                                from services.prospector import obtener_detalle as _det
                                detalle = _det(place_id)
                                if detalle.get("google_photo_url"):
                                    lead["google_photo_url"] = detalle["google_photo_url"]
                            except Exception:
                                pass
                    guardar_leads(leads, SUCURSAL_CODIGO)
                    st.session_state["leads"] = leads
                    st.success(f"✅ {len(_libres)} lead(s) agregados a tus Prospectos.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: EXPORTAR
# ══════════════════════════════════════════════════════════════════════════════

with tab_exportar:
    st.markdown("### Exportar")
    leads_todos = st.session_state.get("leads", [])

    if not leads_todos:
        st.warning("No hay leads.")
    else:
        from services.campaign_exporter import (
            exportar_excel_completo,
            exportar_excel_canal, exportar_seleccion, nombre_archivo
        )

        # ── Filtros de segmentación ────────────────────────────────────────────
        with st.expander("🔽 Filtrar antes de exportar", expanded=True):
            ef1, ef2, ef3 = st.columns(3)
            rubros_exp = sorted(set(l.get("rubro_operativo", "Otro") for l in leads_todos if l.get("rubro_operativo")))
            with ef1:
                f_rubros_exp = st.multiselect("Rubro", rubros_exp, default=rubros_exp, key="exp_f_rubro")
            zonas_exp = sorted(set(l.get("zona", "") for l in leads_todos if l.get("zona")))
            with ef2:
                f_zonas_exp = st.multiselect("Zona", zonas_exp, default=zonas_exp, key="exp_f_zona")
            with ef3:
                f_quality_exp = st.multiselect(
                    "Calidad contacto",
                    ["alta", "media", "baja", "sin_contacto"],
                    default=["alta", "media", "baja", "sin_contacto"],
                    key="exp_f_quality"
                )

        leads = [
            l for l in leads_todos
            if l.get("rubro_operativo", "Otro") in (f_rubros_exp or rubros_exp)
            and l.get("zona", "") in (f_zonas_exp or zonas_exp)
            and l.get("contact_quality", "sin_contacto") in (f_quality_exp or ["alta", "media", "baja", "sin_contacto"])
        ]
        st.caption(f"{len(leads)} leads seleccionados de {len(leads_todos)} totales")
        st.markdown("---")

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.markdown("#### Excel completo")
            st.caption("Hojas: todos, contactables, por canal, para visita, WhatsApp.")
            excel_c = exportar_excel_completo(leads)
            st.download_button(
                "📥 Descargar Excel completo",
                data=excel_c,
                file_name=nombre_archivo("nyper_completo"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )

        with col_e2:
            st.markdown("#### Por canal")
            canales_exp = sorted(set(l.get("primary_channel", "") for l in leads if l.get("primary_channel")))
            for canal in canales_exp:
                ec, n = exportar_excel_canal(leads, canal)
                if n > 0:
                    st.download_button(
                        f"📥 {canal} ({n} leads)",
                        data=ec,
                        file_name=nombre_archivo(f"nyper_{canal}"),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                        key=f"dl_c_{canal}",
                    )

        st.markdown("---")
        st.markdown("#### CSV de campaña (leads con WhatsApp)")
        leads_wa = [l for l in leads if l.get("whatsapp_probable")]
        st.caption(f"{len(leads_wa)} leads con WhatsApp disponibles")

        nombre_camp = st.text_input("Nombre de campaña", placeholder="Ej: Mayo Gastronomía...", key="camp_name")

        if st.button("Exportar CSV campaña", key="btn_csv_camp", use_container_width=True):
            if not nombre_camp.strip():
                st.warning("Ingresá un nombre de campaña.")
            elif not leads_wa:
                st.warning("No hay leads con WhatsApp probable.")
            else:
                rows = []
                for l in leads_wa:
                    phone = l.get("phone_norm", "")
                    wa_link = ""
                    if phone:
                        if phone.startswith("54"):
                            wa_link = f"https://wa.me/{phone}"
                        elif phone.startswith("11") or phone.startswith("15"):
                            wa_link = f"https://wa.me/549{phone}"
                        else:
                            wa_link = f"https://wa.me/54{phone}"
                    rows.append({
                        "Nombre Comercio": l.get("business_name_raw", ""),
                        "Dirección": l.get("address_norm", "") or l.get("address_raw", ""),
                        "Teléfono": phone,
                        "WhatsApp Link": wa_link,
                        "Email": l.get("email_primary", ""),
                        "Rubro": l.get("rubro_operativo", ""),
                        "Campaña": nombre_camp.strip(),
                    })
                df_camp = pd.DataFrame(rows)
                csv_data = df_camp.to_csv(index=False).encode("utf-8")
                nombre_safe = re.sub(r"[^\w]", "_", nombre_camp.strip().lower())
                st.download_button(
                    "📥 Descargar CSV",
                    csv_data,
                    f"campaña_{nombre_safe}_{datetime.now():%Y%m%d_%H%M}.csv",
                    "text/csv",
                    use_container_width=True,
                    key="dl_csv_camp",
                )
                st.success(f"✅ {len(leads_wa)} leads con WhatsApp listos para campaña")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: PROSPECTOS — Mini-CRM de fichas
# ══════════════════════════════════════════════════════════════════════════════

ESTADOS_PROSPECTO = {
    "por_contactar": "🔵 Por contactar",
    "contactado":    "🟡 Contactado",
    "interesado":    "🟢 Interesado",
    "no_interesado": "🔴 No interesado",
}

with tab_prospectos:
    st.markdown("### Prospectos")
    leads = st.session_state.get("leads", [])
    prospectos = [l for l in leads if l.get("en_prospectos")]

    if not prospectos:
        st.info("No hay prospectos todavía. Seleccioná leads en **Bandeja** y presioná **Agregar a Prospectos**.")
    else:
        # Buscador
        busq_pr = st.text_input(
            "🔍 Buscar prospecto",
            placeholder="Nombre, rubro, dirección...",
            key="pr_buscar",
            label_visibility="collapsed",
        )

        # Filtros colapsados — todos desactivados por default (vacío = sin filtro)
        with st.expander("Filtros", expanded=False):
            pf1, pf2, pf3 = st.columns(3)
            with pf1:
                f_est = st.multiselect(
                    "Estado",
                    options=list(ESTADOS_PROSPECTO.keys()),
                    format_func=lambda x: ESTADOS_PROSPECTO[x],
                    default=[],
                    key="pr_f_estado",
                    placeholder="Todos",
                )
            with pf2:
                rubros_pr = sorted(set(l.get("rubro_operativo", "Otro") for l in prospectos))
                f_rub_pr = st.multiselect("Rubro", rubros_pr, default=[], key="pr_f_rubro", placeholder="Todos")
            with pf3:
                f_owner = st.selectbox("Gestor", ["Mis prospectos", "Todos", "Sin asignar"], key="pr_f_owner")

        prospectos_filtrados = prospectos[:]
        if f_est:
            prospectos_filtrados = [l for l in prospectos_filtrados if l.get("prospecto_estado", "por_contactar") in f_est]
        if f_rub_pr:
            prospectos_filtrados = [l for l in prospectos_filtrados if l.get("rubro_operativo", "Otro") in f_rub_pr]
        if f_owner == "Mis prospectos":
            prospectos_filtrados = [l for l in prospectos_filtrados if l.get("owner_email") == usuario["email"]]
        elif f_owner == "Sin asignar":
            prospectos_filtrados = [l for l in prospectos_filtrados if not l.get("owner_email")]

        # Aplicar búsqueda
        if busq_pr:
            _q = busq_pr.lower()
            prospectos_filtrados = [
                l for l in prospectos_filtrados
                if _q in (l.get("business_name_raw", "") or "").lower()
                or _q in (l.get("rubro_operativo", "") or "").lower()
                or _q in (l.get("address_raw", "") or "").lower()
                or _q in (l.get("address_norm", "") or "").lower()
                or _q in (l.get("zona", "") or "").lower()
            ]

        st.caption(f"Mostrando {len(prospectos_filtrados)} de {len(prospectos)} prospectos")
        st.divider()

        # Cards — 2 por fila
        for i in range(0, len(prospectos_filtrados), 2):
            cols_card = st.columns(2)
            for j, col_card in enumerate(cols_card):
                if i + j >= len(prospectos_filtrados):
                    break
                lead = prospectos_filtrados[i + j]
                lead_key = lead.get("lead_id", f"{i+j}")

                with col_card:
                    with st.container(border=True):
                        # Foto si tiene
                        foto_url = lead.get("google_photo_url", "")
                        if foto_url:
                            st.image(foto_url, width=100)

                        # Ownership check
                        _owner_email = lead.get("owner_email", "")
                        _mi_email = usuario["email"]
                        _es_mio = _owner_email == _mi_email or not _owner_email
                        _puede_editar = _es_mio or es_admin()

                        # Encabezado + badge dueño
                        st.markdown(f"**{lead.get('business_name_raw', '—')}**")
                        _caption_extra = f"{lead.get('rubro_operativo', '')} · {lead.get('zona', '')}"
                        st.caption(_caption_extra)
                        if _owner_email:
                            _o_nombre = lead.get("owner_nombre", "")
                            _o_color = lead.get("owner_color", "#3b82f6")
                            if _owner_email == _mi_email:
                                st.markdown(f'<span style="background:{_o_color};color:#fff;padding:2px 10px;border-radius:12px;font-size:.75rem;font-weight:600">📌 Mío</span>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span style="background:{_o_color};color:#fff;padding:2px 10px;border-radius:12px;font-size:.75rem;font-weight:600">🔒 {_o_nombre}</span>', unsafe_allow_html=True)

                        # Datos de contacto con links de acción
                        from urllib.parse import quote as _quote
                        from services.message_templates import generar_mensaje as _gen_msg
                        _suc_nombre = st.session_state.get("sucursal_sel", "").split(" — ")[-1] if " — " in st.session_state.get("sucursal_sel", "") else st.session_state.get("sucursal_sel", "")
                        _usr_nombre = st.session_state.get("nombre_usuario", "")

                        tel = lead.get("phone_raw", "")
                        phone_norm = lead.get("phone_norm", "")
                        if tel:
                            if lead.get("whatsapp_probable") and phone_norm:
                                _wa_data = _gen_msg(lead, "whatsapp", _suc_nombre, _usr_nombre)
                                _wa_num = phone_norm if phone_norm.startswith("54") else f"54{phone_norm}"
                                _wa_url = f"https://wa.me/{_wa_num}?text={_quote(_wa_data['texto'])}"
                                st.markdown(f"<a href='{_wa_url}' target='_blank'><img src='https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg' width='18' style='vertical-align:middle'></a> [{tel}]({_wa_url})", unsafe_allow_html=True)
                            else:
                                st.markdown(f"📞 `{tel}`")
                        if lead.get("email_primary"):
                            _mail_data = _gen_msg(lead, "email", _suc_nombre, _usr_nombre)
                            _asunto_enc = _quote(_mail_data['asunto'], safe='')
                            _cuerpo_enc = _quote(_mail_data['cuerpo'], safe='')
                            _mailto = f"mailto:{lead['email_primary']}?subject={_asunto_enc}&amp;body={_cuerpo_enc}"
                            st.markdown(f'<a href="{_mailto}">📧 {lead["email_primary"]}</a>', unsafe_allow_html=True)
                        if lead.get("website"):
                            st.markdown(f"🌐 [{lead['website']}]({lead['website']})")
                        if lead.get("instagram_url"):
                            st.markdown(f"<a href=\"{lead['instagram_url']}\" target='_blank'><img src='https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png' width='16' style='vertical-align:middle'></a> [Instagram]({lead['instagram_url']})", unsafe_allow_html=True)
                        if lead.get("facebook_url"):
                            st.markdown(f"<a href=\"{lead['facebook_url']}\" target='_blank'><img src='https://upload.wikimedia.org/wikipedia/commons/0/05/Facebook_Logo_%282019%29.png' width='16' style='vertical-align:middle'></a> [Facebook]({lead['facebook_url']})", unsafe_allow_html=True)
                        if lead.get("maps_url"):
                            st.markdown(f"📍 [Ver en Maps]({lead['maps_url']})")

                        st.divider()

                        # Estado de gestión
                        estado_actual = lead.get("prospecto_estado", "por_contactar")
                        if estado_actual not in ESTADOS_PROSPECTO:
                            estado_actual = "por_contactar"
                        nuevo_estado = st.selectbox(
                            "Estado",
                            options=list(ESTADOS_PROSPECTO.keys()),
                            format_func=lambda x: ESTADOS_PROSPECTO[x],
                            index=list(ESTADOS_PROSPECTO.keys()).index(estado_actual),
                            key=f"pr_estado_{lead_key}",
                            disabled=not _puede_editar,
                        )
                        if nuevo_estado != estado_actual and _puede_editar:
                            lead["prospecto_estado"] = nuevo_estado
                            # Ownership: al contactar, se asigna dueño
                            if nuevo_estado in ("contactado", "interesado") and not lead.get("owner_email"):
                                from services.db import registrar_ownership
                                registrar_ownership(lead_key, SUCURSAL_CODIGO, _mi_email)
                                lead["owner_email"] = _mi_email
                                lead["owner_nombre"] = f"{usuario['nombre']} {usuario['apellido']}"
                                lead["owner_color"] = usuario.get("color", "#3b82f6")
                            guardar_leads(leads, SUCURSAL_CODIGO)
                            st.session_state["leads"] = leads

                        # Nota libre
                        nota_actual = lead.get("prospecto_notas", "")
                        nota = st.text_area(
                            "Nota",
                            value=nota_actual,
                            placeholder="Ej: llamé, no atendió. Volver lunes.",
                            height=80,
                            key=f"pr_nota_{lead_key}",
                            label_visibility="collapsed",
                            disabled=not _puede_editar,
                        )
                        if nota != nota_actual and _puede_editar:
                            lead["prospecto_notas"] = nota
                            guardar_leads(leads, SUCURSAL_CODIGO)
                            st.session_state["leads"] = leads

                        # Pasar a Mi Cartera (solo gestor, estados avanzados)
                        if _es_mio and _owner_email and estado_actual in ("contactado", "interesado") and not lead.get("en_cartera"):
                            if st.button("📋 Pasar a Mi Cartera", key=f"pr_cartera_{lead_key}", use_container_width=True):
                                from services.db import guardar_cliente_cartera
                                datos_cartera = {
                                    "nombre_razon_social": lead.get("business_name_raw", ""),
                                    "cuit": lead.get("cuit", ""),
                                    "rubro": lead.get("rubro_operativo", ""),
                                    "telefono": lead.get("phone_raw", ""),
                                    "mail": lead.get("email_primary", ""),
                                    "direccion": lead.get("address_norm", "") or lead.get("address_raw", ""),
                                    "localidad": lead.get("zona", ""),
                                    "observaciones": lead.get("prospecto_notas", ""),
                                }
                                guardar_cliente_cartera(_mi_email, datos_cartera)
                                lead["en_cartera"] = True
                                guardar_leads(leads, SUCURSAL_CODIGO)
                                st.session_state["leads"] = leads
                                st.success("Agregado a Mi Cartera")
                                st.rerun()
                        elif lead.get("en_cartera"):
                            st.markdown('<span style="background:#e8f5ee;color:#00A651;padding:2px 10px;border-radius:12px;font-size:.75rem;font-weight:600">✅ En cartera</span>', unsafe_allow_html=True)

                        # Quitar de prospectos (solo gestor o admin)
                        if _puede_editar:
                            if st.button("✖ Quitar de Prospectos", key=f"pr_quitar_{lead_key}"):
                                lead["en_prospectos"] = False
                                lead["prospecto_estado"] = ""
                                if lead.get("owner_email"):
                                    from services.db import eliminar_ownership
                                    eliminar_ownership(lead_key, SUCURSAL_CODIGO)
                                lead.pop("owner_email", None)
                                lead.pop("owner_nombre", None)
                                lead.pop("owner_color", None)
                                guardar_leads(leads, SUCURSAL_CODIGO)
                                st.session_state["leads"] = leads
                                st.rerun()

        # KPIs al final
        st.divider()
        st.markdown("#### Resumen")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total", len(prospectos))
        c2.metric("Míos", sum(1 for l in prospectos if l.get("owner_email") == usuario["email"]))
        c3.metric("Por contactar", sum(1 for l in prospectos if l.get("prospecto_estado") == "por_contactar"))
        c4.metric("Contactados", sum(1 for l in prospectos if l.get("prospecto_estado") == "contactado"))
        c5.metric("Interesados", sum(1 for l in prospectos if l.get("prospecto_estado") == "interesado"))
        c6.metric("No interesados", sum(1 for l in prospectos if l.get("prospecto_estado") == "no_interesado"))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: ANÁLISIS
# ══════════════════════════════════════════════════════════════════════════════

with tab_analisis:
    st.markdown("### Análisis")
    leads = st.session_state.get("leads", [])

    if not leads:
        st.warning("No hay leads.")
    else:
        import altair as alt

        total = len(leads)
        contactables = sum(1 for l in leads if l.get("contact_available"))
        vigentes = sum(1 for l in leads if l.get("vigencia_digital") == "vigente")
        wa = sum(1 for l in leads if l.get("whatsapp_probable"))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", total)
        c2.metric("Contactables", contactables)
        c3.metric("Vigentes", vigentes)
        c4.metric("WhatsApp", wa)

        st.divider()

        # ── Resumen ejecutivo ──────────────────────────────────────────────────
        llamada = sum(1 for l in leads if l.get("primary_channel") == "llamada")
        rubros_count = {}
        for l in leads:
            r = l.get("rubro_operativo", "Otro")
            rubros_count[r] = rubros_count.get(r, 0) + 1
        rubros_ord = sorted(rubros_count.items(), key=lambda x: -x[1])
        rubro1, n1 = rubros_ord[0] if rubros_ord else ("—", 0)
        rubro2, n2 = rubros_ord[1] if len(rubros_ord) > 1 else ("—", 0)

        zonas_count = {}
        for l in leads:
            z = l.get("zona", "Sin zona")
            zonas_count[z] = zonas_count.get(z, 0) + 1
        zona_principal = max(zonas_count, key=zonas_count.get) if zonas_count else "—"

        st.info(
            f"**{total} comercios** detectados en el territorio de la sucursal. "
            f"**{contactables}** contactables — **{wa}** por WhatsApp, **{llamada}** por llamada. "
            f"Rubros dominantes: **{rubro1}** ({n1}) y **{rubro2}** ({n2}). "
            f"Concentración principal en **{zona_principal}**."
        )

        st.divider()

        # ── Gráficos ───────────────────────────────────────────────────────────
        col_an1, col_an2 = st.columns(2)

        with col_an1:
            st.markdown("**Canales de contacto**")
            canales = {}
            for l in leads:
                cv = l.get("primary_channel", "sin_canal")
                canales[cv] = canales.get(cv, 0) + 1
            canales_etiquetas = {
                "whatsapp": "WhatsApp",
                "llamada": "Llamada",
                "mail": "Mail",
                "redes": "Redes",
                "visita": "Visita",
                "sin_canal": "Sin canal",
            }
            colores_canal_an = {
                "WhatsApp": "#25D366",
                "Llamada": "#3b82f6",
                "Mail": "#f97316",
                "Redes": "#a855f7",
                "Visita": "#6b7280",
                "Sin canal": "#9ca3af",
            }
            df_canales = pd.DataFrame([
                {"Canal": canales_etiquetas.get(k, k), "Leads": v}
                for k, v in sorted(canales.items(), key=lambda x: -x[1])
            ])
            if not df_canales.empty:
                chart_dona = alt.Chart(df_canales).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta("Leads:Q"),
                    color=alt.Color(
                        "Canal:N",
                        scale=alt.Scale(
                            domain=list(colores_canal_an.keys()),
                            range=list(colores_canal_an.values()),
                        ),
                        legend=alt.Legend(orient="bottom"),
                    ),
                    tooltip=["Canal:N", "Leads:Q"],
                ).properties(height=280)
                st.altair_chart(chart_dona, use_container_width=True)

        with col_an2:
            st.markdown("**Top 10 rubros**")
            rubros_top = rubros_ord[:10]
            df_rubros = pd.DataFrame([{"Rubro": k, "Leads": v} for k, v in rubros_top])
            if not df_rubros.empty:
                chart_rubros = alt.Chart(df_rubros).mark_bar(color="#00A651").encode(
                    x=alt.X("Leads:Q", title=""),
                    y=alt.Y("Rubro:N", sort="-x", title=""),
                    tooltip=["Rubro:N", "Leads:Q"],
                ).properties(height=280)
                st.altair_chart(chart_rubros, use_container_width=True)

        # ── Tabla por zona (solo si hay más de 1) ──────────────────────────────
        if len(zonas_count) > 1:
            st.divider()
            st.markdown("**Por zona**")
            st.dataframe(
                pd.DataFrame([{"Zona": k, "Leads": v} for k, v in sorted(zonas_count.items(), key=lambda x: -x[1])]),
                width="stretch", hide_index=True
            )

        # ── Sección Prospectos ────────────────────────────────────────────────
        prospectos_an = [l for l in leads if l.get("en_prospectos")]
        if prospectos_an:
            st.divider()
            st.markdown("""
            <div style="background:linear-gradient(135deg,#e0f7fa,#b2ebf2);border-radius:12px;padding:1.5rem;margin-bottom:1rem">
                <h4 style="margin:0;color:#006064">⭐ Prospectos</h4>
                <p style="margin:0.3rem 0 0 0;color:#00838f;font-size:0.9rem">Resumen de leads en gestión activa</p>
            </div>
            """, unsafe_allow_html=True)

            total_pr = len(prospectos_an)
            estados_orden = ["por_contactar", "contactado", "interesado", "no_interesado"]
            estados_nombres = {
                "por_contactar": "Por contactar",
                "contactado": "Contactado",
                "interesado": "Interesado",
                "no_interesado": "No interesado",
            }
            estados_colores = {
                "Por contactar": "#3b82f6",
                "Contactado": "#eab308",
                "Interesado": "#22c55e",
                "No interesado": "#ef4444",
            }
            conteos_estado = {
                estados_nombres[e]: sum(1 for l in prospectos_an if l.get("prospecto_estado") == e)
                for e in estados_orden
            }

            # KPIs rápidos
            cp1, cp2, cp3, cp4 = st.columns(4)
            cp1.metric("Prospectos", total_pr)
            cp2.metric("Por contactar", conteos_estado["Por contactar"])
            cp3.metric("Contactados", conteos_estado["Contactado"])
            cp4.metric("Interesados", conteos_estado["Interesado"])

            col_emb, col_rub = st.columns(2)

            with col_emb:
                st.markdown("**Embudo de gestión**")
                df_embudo = pd.DataFrame([
                    {"Estado": k, "Cantidad": v, "Orden": i}
                    for i, (k, v) in enumerate(conteos_estado.items())
                ])
                chart_embudo = alt.Chart(df_embudo).mark_bar().encode(
                    x=alt.X("Cantidad:Q", title=""),
                    y=alt.Y("Estado:N", sort=alt.EncodingSortField(field="Orden"), title=""),
                    color=alt.Color("Estado:N", scale=alt.Scale(
                        domain=list(estados_colores.keys()),
                        range=list(estados_colores.values()),
                    ), legend=None),
                    tooltip=["Estado:N", "Cantidad:Q"],
                ).properties(height=180)
                st.altair_chart(chart_embudo, use_container_width=True)

            with col_rub:
                st.markdown("**Prospectos por rubro**")
                rubros_pr = {}
                for l in prospectos_an:
                    r = l.get("rubro_operativo", "Otro")
                    rubros_pr[r] = rubros_pr.get(r, 0) + 1
                df_rubros_pr = pd.DataFrame([
                    {"Rubro": k, "Prospectos": v}
                    for k, v in sorted(rubros_pr.items(), key=lambda x: -x[1])[:8]
                ])
                if not df_rubros_pr.empty:
                    chart_rubros_pr = alt.Chart(df_rubros_pr).mark_bar(color="#00bcd4").encode(
                        x=alt.X("Prospectos:Q", title=""),
                        y=alt.Y("Rubro:N", sort="-x", title=""),
                        tooltip=["Rubro:N", "Prospectos:Q"],
                    ).properties(height=200)
                    st.altair_chart(chart_rubros_pr, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<hr style="margin-top:2rem">
<div class="global-footer" style="text-align:center;padding:1.5rem 0;font-family:'Montserrat',sans-serif">
  {_FIRMA_HTML}
  <div style="color:#4a5568;font-size:.75rem;margin-top:.8rem">
    NyPer v4.0 · Banco Provincia
  </div>
</div>
""", unsafe_allow_html=True)
