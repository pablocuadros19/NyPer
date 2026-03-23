"""
Semáforo por reglas duras. No scoring numérico.
Clasifica prospectos en rojo/amarillo/verde/verde_destacado con motivos.
"""


# Rubros con alta demanda bancaria
RUBROS_ALTA_DEMANDA = {
    "Construcción", "Taller mecánico", "Concesionaria", "Estación de servicio",
    "Salud", "Odontología", "Supermercado", "Ferretería", "Electrónica",
    "Centro comercial", "Alojamiento",
}


def clasificar_semaforo(comercio: dict) -> dict:
    """
    Aplica reglas duras y devuelve semáforo + motivos.
    Modifica el comercio in-place y lo retorna.
    gris = sin datos suficientes para clasificar.
    """
    motivos = []
    red_flags = []

    # --- Datos disponibles ---
    tiene_cuit = bool(comercio.get("cuit"))
    bcra_sit = comercio.get("bcra_situacion", -1)
    bcra_consultado = comercio.get("bcra_consultado", False)
    cheques = comercio.get("bcra_cheques_rechazados", 0)
    deuda_bapro = comercio.get("deuda_bapro", False)
    arca_estado = comercio.get("arca_estado_clave", "")
    arca_consultado = comercio.get("arca_consultado", False)
    arca_empleador = comercio.get("arca_empleador", False)
    arca_iva = comercio.get("arca_condicion_iva", "")
    bcra_evolucion = comercio.get("bcra_evolucion", "")
    proceso_concursal = comercio.get("bcra_proceso_concursal", False)
    rubro = comercio.get("rubro", "")

    # --- GRIS: sin datos suficientes ---
    if not tiene_cuit:
        comercio["semaforo"] = "gris"
        comercio["semaforo_motivos"] = ["Sin CUIT — no se puede verificar"]
        return comercio

    if not arca_consultado and not bcra_consultado:
        comercio["semaforo"] = "gris"
        comercio["semaforo_motivos"] = ["CUIT sin consultar en ARCA/BCRA"]
        return comercio

    # --- RED FLAGS → ROJO automático ---

    if deuda_bapro:
        red_flags.append("Deuda con Banco Provincia")

    if bcra_sit >= 4:
        red_flags.append(f"BCRA situación {bcra_sit} (irrecuperable)")

    if arca_estado in ("INACTIVO", "SUSPENDIDO"):
        red_flags.append(f"CUIT {arca_estado} en ARCA")

    if proceso_concursal:
        red_flags.append("Proceso concursal activo")

    if red_flags:
        comercio["semaforo"] = "rojo"
        comercio["semaforo_motivos"] = red_flags
        return comercio

    # --- AMARILLO: señales de alerta no fatales ---

    if bcra_sit in (2, 3):
        sit_texto = "con seguimiento" if bcra_sit == 2 else "con problemas"
        motivos.append(f"BCRA situación {bcra_sit} ({sit_texto})")

    if isinstance(cheques, int) and cheques > 0:
        motivos.append(f"Cheques rechazados: {cheques}")

    if bcra_evolucion == "empeorando":
        motivos.append("BCRA empeorando vs período anterior")

    if not bcra_consultado and comercio.get("cuit"):
        motivos.append("BCRA no consultado (sin datos)")

    if arca_estado == "NO_ENCONTRADO":
        motivos.append("CUIT no encontrado en ARCA")

    if motivos:
        comercio["semaforo"] = "amarillo"
        comercio["semaforo_motivos"] = motivos
        return comercio

    # --- VERDE: limpio ---

    # Verificar si califica como destacado
    señales_positivas = 0

    if arca_empleador:
        señales_positivas += 1

    if arca_iva == "Responsable Inscripto":
        señales_positivas += 1

    if bcra_sit == 0 and bcra_consultado:
        señales_positivas += 1

    if rubro in RUBROS_ALTA_DEMANDA:
        señales_positivas += 1

    if señales_positivas >= 2:
        comercio["semaforo"] = "verde_destacado"
        razones = []
        if arca_empleador:
            razones.append("Empleador")
        if arca_iva == "Responsable Inscripto":
            razones.append("Resp. Inscripto")
        if bcra_sit == 0 and bcra_consultado:
            razones.append("BCRA limpio")
        if rubro in RUBROS_ALTA_DEMANDA:
            razones.append(f"Rubro fuerte ({rubro})")
        comercio["semaforo_motivos"] = razones
    else:
        comercio["semaforo"] = "verde"
        comercio["semaforo_motivos"] = ["Sin alertas"]

    return comercio


def clasificar_batch(comercios: list) -> list:
    """Aplica semáforo a toda la lista."""
    for c in comercios:
        clasificar_semaforo(c)
    return comercios


def resumen_semaforos(comercios: list) -> dict:
    """Retorna conteo por color."""
    resumen = {"rojo": 0, "amarillo": 0, "verde": 0, "verde_destacado": 0, "gris": 0, "sin_clasificar": 0}
    for c in comercios:
        s = c.get("semaforo", "sin_clasificar")
        resumen[s] = resumen.get(s, 0) + 1
    return resumen


# --- Test ---
if __name__ == "__main__":
    casos = [
        {
            "nombre": "Caso 1: Verde destacado",
            "bcra_situacion": 0, "bcra_consultado": True,
            "bcra_cheques_rechazados": 0, "deuda_bapro": False,
            "arca_estado_clave": "ACTIVO", "arca_consultado": True,
            "arca_empleador": True, "arca_condicion_iva": "Responsable Inscripto",
            "rubro": "Construcción",
        },
        {
            "nombre": "Caso 2: Verde simple",
            "bcra_situacion": 0, "bcra_consultado": True,
            "bcra_cheques_rechazados": 0, "deuda_bapro": False,
            "arca_estado_clave": "ACTIVO", "arca_consultado": True,
            "arca_empleador": False, "arca_condicion_iva": "Monotributo",
            "rubro": "Cafetería",
        },
        {
            "nombre": "Caso 3: Amarillo - cheques",
            "bcra_situacion": 1, "bcra_consultado": True,
            "bcra_cheques_rechazados": 3, "deuda_bapro": False,
            "arca_estado_clave": "ACTIVO", "arca_consultado": True,
            "arca_empleador": True, "arca_condicion_iva": "Responsable Inscripto",
            "rubro": "Ferretería",
        },
        {
            "nombre": "Caso 4: Rojo - deuda bapro",
            "bcra_situacion": 1, "bcra_consultado": True,
            "deuda_bapro": True,
        },
        {
            "nombre": "Caso 5: Rojo - CUIT inactivo",
            "arca_estado_clave": "INACTIVO", "arca_consultado": True,
            "bcra_situacion": 0, "bcra_consultado": True,
        },
    ]

    for caso in casos:
        nombre = caso.pop("nombre")
        clasificar_semaforo(caso)
        print(f"{nombre}")
        print(f"  Semáforo: {caso['semaforo']}")
        print(f"  Motivos: {caso['semaforo_motivos']}")
        print()
