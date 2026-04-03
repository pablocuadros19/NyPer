"""
Genera el manual de usuario de NyPer en PDF.
Ejecutar: python docs/generar_manual_pdf.py
Salida: docs/Manual_NyPer.pdf
"""
import os
import sys

# Asegurar encoding UTF-8 en Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fpdf import FPDF

# Ruta base del proyecto
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")
OUT = os.path.join(BASE, "docs", "Manual_NyPer.pdf")


class ManualPDF(FPDF):
    """PDF personalizado con header/footer estilo NyPer."""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 166, 81)
        self.cell(0, 8, "NyPer - Manual de Usuario", align="L")
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "Banco Provincia", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 166, 81)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Pag {self.page_no()}/{{nb}}", align="C")

    def titulo_seccion(self, num, texto):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 166, 81)
        self.ln(6)
        self.cell(0, 10, f"{num}. {texto}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 166, 81)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def subtitulo(self, texto):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 30, 46)
        self.ln(3)
        self.cell(0, 8, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def parrafo(self, texto):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, texto)
        self.ln(2)

    def item(self, texto, bold_prefix=""):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.cell(8, 6, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 10)
            self.cell(self.get_string_width(bold_prefix) + 2, 6, bold_prefix)
            self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, texto)
        self.ln(1)

    def nota(self, texto):
        self.set_fill_color(240, 249, 244)
        self.set_draw_color(200, 230, 213)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(0, 130, 60)
        self.set_x(10)
        y = self.get_y()
        # Calcular alto necesario
        n_lines = len(self.multi_cell(182, 5, texto, dry_run=True, output="LINES"))
        h = max(14, n_lines * 5 + 4)
        self.rect(10, y, 190, h, style="DF")
        self.set_xy(14, y + 2)
        self.multi_cell(182, 5, texto)
        self.ln(4)

    def tabla_simple(self, headers, rows):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 166, 81)
        self.set_text_color(255, 255, 255)
        col_w = 190 / len(headers)
        for h in headers:
            self.cell(col_w, 8, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(247, 249, 252)
            else:
                self.set_fill_color(255, 255, 255)
            for val in row:
                self.cell(col_w, 7, str(val), border=1, fill=True, align="C")
            self.ln()
            fill = not fill
        self.ln(3)


def generar():
    pdf = ManualPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Portada ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(30)

    # Logo si existe
    logo_path = os.path.join(ASSETS, "logo_nyper.png")
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=55, w=100)
        pdf.ln(10)

    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(0, 166, 81)
    pdf.cell(0, 20, "NyPer", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Manual de Usuario", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_draw_color(0, 166, 81)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Inteligencia Comercial Territorial", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Banco Provincia", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, "Version 4.0 - Abril 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # ── Indice ────────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(0, 166, 81)
    pdf.cell(0, 12, "Indice", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    indice = [
        ("1", "Que es NyPer"),
        ("2", "Acceso al sistema"),
        ("3", "Pantalla principal"),
        ("4", "Modulo: Buscar Clientes"),
        ("  4.1", "Inicio"),
        ("  4.2", "Descubrir"),
        ("  4.3", "Enriquecer"),
        ("  4.4", "Bandeja operativa"),
        ("  4.5", "Exportar"),
        ("  4.6", "Prospectos"),
        ("  4.7", "Analisis"),
        ("5", "Modulo: Mi Cartera"),
        ("  5.1", "KPIs y vista general"),
        ("  5.2", "Carga manual de clientes"),
        ("  5.3", "Importar Informe Roles"),
        ("  5.4", "Importar Excel generico"),
        ("  5.5", "Editar clientes y criterios"),
        ("6", "Sistema de gestores (ownership)"),
        ("7", "Panel de administracion"),
        ("8", "Preguntas frecuentes"),
    ]
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    for num, titulo in indice:
        indent = 20 if num.startswith(" ") else 0
        pdf.set_x(15 + indent)
        peso = "" if num.startswith(" ") else "B"
        pdf.set_font("Helvetica", peso, 11)
        pdf.cell(0, 7, f"{num.strip()}   {titulo}", new_x="LMARGIN", new_y="NEXT")

    # ── 1. Que es NyPer ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("1", "Que es NyPer")
    pdf.parrafo(
        "NyPer es una herramienta de inteligencia comercial territorial disenada para "
        "los Roles NyP (Negocios y Profesionales) del Banco Provincia. Su objetivo es "
        "transformar el territorio de cada sucursal en oportunidades comerciales accionables."
    )
    pdf.parrafo(
        "La herramienta trabaja exclusivamente con fuentes publicas de informacion "
        "(Google Places, ARCA/AFIP, BCRA, sitios web publicos). No consulta bases internas "
        "de clientes ni requiere integracion con sistemas core del banco."
    )
    pdf.subtitulo("Que podes hacer con NyPer")
    pdf.item("Descubrir comercios, pymes y profesionales cerca de tu sucursal", "Descubrir: ")
    pdf.item("Enriquecer la informacion con telefono, email, redes sociales, CUIT, BCRA", "Enriquecer: ")
    pdf.item("Priorizar los leads por contactabilidad y canal de contacto", "Priorizar: ")
    pdf.item("Gestionar prospectos como un mini-CRM con estados y notas", "Gestionar: ")
    pdf.item("Exportar listados listos para campanias de WhatsApp, mail o visita", "Exportar: ")
    pdf.item("Administrar tu cartera personal con criterios comerciales del Informe Roles", "Mi Cartera: ")

    pdf.nota("NyPer no reemplaza al SGI ni a los sistemas del banco. Es una herramienta complementaria de apoyo territorial.")

    # ── 2. Acceso al sistema ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("2", "Acceso al sistema")

    pdf.subtitulo("Login")
    pdf.parrafo(
        "Al abrir NyPer vas a ver la pantalla de login. Ingresa tu email corporativo "
        "(@bpba.com.ar) y la contrasena que te dio el administrador."
    )
    pdf.item("Solo se aceptan emails con dominio @bpba.com.ar")
    pdf.item("Si no tenes usuario, pedile al administrador que te cree uno")
    pdf.item("Despues del login vas a ver un mensaje de bienvenida por 3 segundos")

    pdf.subtitulo("Sesion persistente")
    pdf.parrafo(
        "Tu sesion se mantiene activa aunque actualices la pagina (F5). "
        "No necesitas volver a loguearte cada vez que recargues."
    )

    pdf.subtitulo("Cerrar sesion")
    pdf.parrafo(
        "El boton 'Cerrar sesion' esta arriba a la derecha en todas las pantallas. "
        "Al cerrar sesion se elimina tu token y volves a la pantalla de login."
    )

    # ── 3. Pantalla principal ────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("3", "Pantalla principal")
    pdf.parrafo(
        "Despues del login y la bienvenida, llegues a la pantalla principal con dos "
        "grandes opciones:"
    )

    pdf.subtitulo("Buscar Clientes")
    pdf.parrafo(
        "Accede al modulo completo de NyPer con 7 pestanias: Inicio, Descubrir, "
        "Enriquecer, Bandeja, Exportar, Prospectos y Analisis. Aca descubris "
        "comercios en tu zona, los enriqueces con datos de contacto y los gestionas."
    )

    pdf.subtitulo("Mi Cartera")
    pdf.parrafo(
        "Tu cartera personal de clientes. Podes cargar clientes manualmente, "
        "importar el Informe Roles del banco, y ver los criterios comerciales "
        "que cumple cada cliente."
    )

    pdf.nota("El boton '<< Inicio' arriba a la izquierda te lleva de vuelta a esta pantalla desde cualquier modulo.")

    # ── 4. Modulo Buscar Clientes ────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("4", "Modulo: Buscar Clientes")
    pdf.parrafo(
        "Este es el corazon de NyPer. Tiene 7 pestanias que representan el flujo "
        "de trabajo completo: desde descubrir comercios hasta exportar listados "
        "para campanias."
    )
    pdf.parrafo(
        "Al entrar al modulo, arriba vas a ver el header con el logo de NyPer "
        "y un selector de sucursal. Podes buscar tu sucursal por codigo o nombre."
    )

    # 4.1 Inicio
    pdf.subtitulo("4.1 Inicio")
    pdf.parrafo(
        "Pantalla informativa que explica que es NyPer, como funciona el flujo "
        "de trabajo, y cuales son las fuentes de informacion que usa."
    )
    pdf.parrafo(
        "Si sos administrador, aca tambien vas a ver el panel de Administracion "
        "(ver seccion 7)."
    )

    # 4.2 Descubrir
    pdf.subtitulo("4.2 Descubrir")
    pdf.parrafo(
        "Aca se buscan comercios en la zona de influencia de tu sucursal usando "
        "Google Places API."
    )
    pdf.item("Elegir el radio de busqueda (1 a 10 km)")
    pdf.item("Definir el minimo de resenias (filtra comercios poco relevantes)")
    pdf.item("Seleccionar los rubros que te interesan (Gastronomia, Comercio, Salud, etc.)")
    pdf.item("Presionar 'Buscar comercios ahora'")
    pdf.parrafo(
        "El perrito animado aparece mientras se busca. Los resultados se guardan "
        "automaticamente. Si ya tenes leads, los nuevos se suman sin pisar los "
        "existentes."
    )
    pdf.nota("Los leads nuevos se cruzan automaticamente con la base de Cuenta DNI para detectar comercios que ya la tienen.")

    # 4.3 Enriquecer
    if pdf.get_y() > 220:
        pdf.add_page()
    pdf.subtitulo("4.3 Enriquecer")
    pdf.parrafo(
        "Enriquece los datos de tus leads en 3 pasos opcionales:"
    )
    pdf.item(
        "Busca telefono, email y redes sociales en Google Places Details y scraping de websites.",
        "1. Enriquecer contacto: "
    )
    pdf.item(
        "Extrae emails y redes de los sitios web de los comercios que tengan URL.",
        "2. Rastrear websites: "
    )
    pdf.item(
        "Resuelve CUITs (cruce con Registro de Sociedades), consulta ARCA y BCRA. "
        "Tambien cruza con base LICITARG de proveedores del estado.",
        "3. Enriquecimiento profundo: "
    )
    pdf.parrafo(
        "Cada paso muestra una barra de progreso y el perrito olfateando. "
        "Los datos se guardan automaticamente cada 50 leads procesados."
    )

    # 4.4 Bandeja
    pdf.add_page()
    pdf.subtitulo("4.4 Bandeja operativa")
    pdf.parrafo(
        "La bandeja es el centro de operaciones. Muestra todos los leads en una "
        "tabla interactiva con mapa geografico."
    )
    pdf.item("Mapa con pines de colores segun canal de contacto (verde=WhatsApp, azul=llamada, naranja=mail, violeta=redes, gris=sin canal)")
    pdf.item("Tabla con columnas: Nombre, Rubro, Zona, Canal, Telefono, Email, Web, IG, CDNI, Gestor, Rating")

    pdf.parrafo("Filtros disponibles:")
    pdf.item("Canal de contacto")
    pdf.item("Rubro")
    pdf.item("Zona geografica")
    pdf.item("Contactable (si/no)")
    pdf.item("Vigente (actividad digital reciente)")
    pdf.item("Duplicados (ocultar/mostrar/solo duplicados)")
    pdf.item("Cuenta DNI (con/sin)")
    pdf.item("Gestor (todos/mis leads/sin asignar)")

    pdf.parrafo(
        "Podes seleccionar leads en la tabla y presionar 'Agregar a Prospectos' "
        "para pasarlos al mini-CRM."
    )

    # 4.5 Exportar
    if pdf.get_y() > 200:
        pdf.add_page()
    pdf.subtitulo("4.5 Exportar")
    pdf.parrafo("Genera archivos listos para usar:")
    pdf.item("Excel completo con multiples hojas (todos, contactables, por canal, para visita, WhatsApp)", "Excel completo: ")
    pdf.item("Excel por canal individual (un archivo por cada canal de contacto)", "Por canal: ")
    pdf.item("CSV de campania con nombre de campania, link de WhatsApp directo, telefono y email", "CSV campania: ")
    pdf.parrafo(
        "Antes de exportar podes filtrar por rubro, zona y calidad de contacto."
    )

    # 4.6 Prospectos
    pdf.add_page()
    pdf.subtitulo("4.6 Prospectos (Mini-CRM)")
    pdf.parrafo(
        "Los prospectos son los leads que seleccionaste para gestionar activamente. "
        "Se muestran como fichas (cards) con toda la informacion del comercio."
    )
    pdf.parrafo("Cada ficha incluye:")
    pdf.item("Foto del comercio (si Google tiene una)")
    pdf.item("Datos de contacto con links directos: WhatsApp (abre chat con mensaje), email (abre mailto con asunto y cuerpo), web, Instagram, Facebook, Google Maps")
    pdf.item("Estado de gestion con 4 opciones:")

    pdf.tabla_simple(
        ["Estado", "Color", "Significado"],
        [
            ["Por contactar", "Azul", "Todavia no lo contacte"],
            ["Contactado", "Amarillo", "Ya hable con el"],
            ["Interesado", "Verde", "Mostro interes"],
            ["No interesado", "Rojo", "No le interesa"],
        ],
    )

    pdf.item("Nota libre para registrar observaciones (ej: 'llame, no atendio. Volver lunes.')")
    pdf.item("Badge de gestor (ver seccion 6)")
    pdf.item("Boton 'Pasar a Mi Cartera' cuando el prospecto esta contactado o interesado")
    pdf.item("Boton 'Quitar de Prospectos' para sacarlo de la lista")

    pdf.parrafo("Filtros: estado, rubro, gestor (todos/mis prospectos/sin asignar). Tambien tiene buscador por nombre, rubro o direccion.")

    # 4.7 Analisis
    if pdf.get_y() > 200:
        pdf.add_page()
    pdf.subtitulo("4.7 Analisis")
    pdf.parrafo(
        "Graficos y metricas sobre tus leads:"
    )
    pdf.item("KPIs: total, contactables, vigentes, WhatsApp")
    pdf.item("Resumen ejecutivo en texto con datos clave")
    pdf.item("Grafico dona: distribucion por canal de contacto")
    pdf.item("Grafico barras: top 10 rubros")
    pdf.item("Tabla por zona geografica")
    pdf.item("Seccion Prospectos: embudo de gestion (por contactar > contactado > interesado > no interesado) y prospectos por rubro")

    # ── 5. Modulo Mi Cartera ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("5", "Modulo: Mi Cartera")
    pdf.parrafo(
        "Tu cartera personal de clientes. Aca gestionas los clientes que ya tenes "
        "asignados, ya sea porque los pasaste desde Prospectos o porque los importaste "
        "desde el Informe Roles."
    )

    pdf.subtitulo("5.1 KPIs y vista general")
    pdf.parrafo("Arriba vas a ver 3 metricas: total de clientes, rubro principal, rubros distintos.")
    pdf.parrafo("Si sos admin podes ver la cartera de cualquier usuario con el selector 'Ver cartera de'.")

    pdf.subtitulo("5.2 Carga manual de clientes")
    pdf.parrafo(
        "Desplegando 'Agregar cliente manual' podes cargar un cliente a mano "
        "completando: nombre/razon social (obligatorio), CUIT, rubro, subrubro, "
        "telefono, email, direccion, localidad, observaciones."
    )

    pdf.subtitulo("5.3 Importar Informe Roles")
    pdf.parrafo(
        "Esta es la funcion principal de Mi Cartera. Importa el archivo Informe Roles "
        "del banco (.xlsb o .xlsx) y carga automaticamente toda tu cartera."
    )
    pdf.item("Tu usuario necesita tener configurado el codigo de afiliado (ej: P047071). Si no lo tenes, pedile al admin.")
    pdf.item("Al importar, NyPer filtra automaticamente los clientes que corresponden a tu afiliado.")
    pdf.item("Se importan: nombre (TITULAR), CUIT, rubro (Desc_Actividad), subrubro (RECIPROCIDAD).")
    pdf.item("Se detectan los 12 criterios comerciales de cada cliente (ver tabla abajo).")

    pdf.nota("IMPORTANTE: Importar el Informe Roles REEMPLAZA toda la cartera anterior. NyPer muestra un informe de diferencias: clientes nuevos, clientes que salieron, y cambios en criterios.")

    if pdf.get_y() > 180:
        pdf.add_page()

    pdf.parrafo("Los 12 criterios comerciales que detecta NyPer:")
    pdf.tabla_simple(
        ["Criterio", "Que mide"],
        [
            ["Acreditacion Cupon", "Acredita cupones de tarjeta"],
            ["ART y Seguros", "Tiene ART o seguros"],
            ["Descuento Cheques", "Descuenta cheques"],
            ["Haberes", "Acredita haberes"],
            ["CDNI Comercio", "Tiene Cuenta DNI comercio"],
            ["Comex", "Opera en comercio exterior"],
            ["Emision/Dep. Echeq", "Emite o deposita echeqs"],
            ["Emp. Proveedora", "Es empresa proveedora"],
            ["Garantias ON", "Tiene garantias ON"],
            ["Inversion Financiera", "Tiene inversiones financieras"],
            ["Pactar", "Usa sistema Pactar"],
            ["Prestamos Inversion", "Tiene prestamos de inversion"],
        ],
    )

    pdf.subtitulo("5.4 Importar Excel generico")
    pdf.parrafo(
        "Si tenes un listado en Excel (.xlsx), podes importarlo desde 'Agregar desde Excel'. "
        "NyPer detecta automaticamente las columnas y agrega los clientes a tu cartera "
        "(no pisa, suma)."
    )

    pdf.subtitulo("5.5 Editar clientes y criterios")
    pdf.parrafo(
        "Cada cliente se muestra como una tarjeta con su scoring de criterios (X/12). "
        "Los criterios que cumple aparecen en verde, los que no en rojo."
    )
    pdf.parrafo(
        "Desplegando 'Editar [nombre]' podes modificar todos los datos del cliente "
        "y marcar/desmarcar criterios comerciales manualmente. Tambien podes eliminar "
        "el cliente."
    )
    pdf.parrafo("El buscador de arriba filtra por nombre, CUIT, rubro o localidad.")

    # ── 6. Sistema de gestores ────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("6", "Sistema de gestores (ownership)")
    pdf.parrafo(
        "NyPer tiene un sistema de asignacion de gestores para evitar que dos roles "
        "trabajen sobre el mismo prospecto."
    )
    pdf.subtitulo("Como funciona")
    pdf.item("Cuando cambias el estado de un prospecto a 'Contactado' o 'Interesado', NyPer te asigna automaticamente como gestor de ese prospecto.")
    pdf.item("Tu badge aparece en la ficha del prospecto con tu color asignado y el icono de pin.")
    pdf.item("Si otro rol ve ese prospecto, le aparece un candado con tu nombre y no puede cambiarle el estado ni las notas.")
    pdf.item("Solo el gestor asignado o un administrador pueden modificar un prospecto ya tomado.")
    pdf.item("Un admin puede reasignar el gestor desde el panel de administracion.")

    pdf.subtitulo("Filtrar por gestor")
    pdf.parrafo(
        "Tanto en Bandeja como en Prospectos tenes un filtro de 'Gestor' con tres opciones: "
        "Todos, Mis prospectos (solo los tuyos), Sin asignar (los que nadie tomo todavia)."
    )

    # ── 7. Panel de administracion ───────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("7", "Panel de administracion (solo admin)")
    pdf.parrafo(
        "El panel de administracion esta en la pestania 'Inicio' del modulo Buscar Clientes. "
        "Solo lo ven los usuarios con rol 'admin'."
    )
    pdf.subtitulo("Usuarios")
    pdf.item(
        "Completar nombre, apellido, email @bpba.com.ar, contrasenia, rol, color, "
        "y codigo de afiliado. El codigo de afiliado es necesario para importar el Informe Roles.",
        "Crear usuario: "
    )
    pdf.item("Muestra todos los usuarios con su estado, rol y codigo de afiliado.", "Listar usuarios: ")
    pdf.item("Boton para activar o desactivar usuarios.", "Activar/Desactivar: ")

    pdf.subtitulo("Reasignar gestores")
    pdf.parrafo(
        "Permite cambiar el gestor de un prospecto asignado. Se muestra la lista "
        "de prospectos con gestor y un selector para elegir el nuevo gestor."
    )

    # ── 8. Preguntas frecuentes ──────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo_seccion("8", "Preguntas frecuentes")

    preguntas = [
        (
            "No me deja importar el Informe Roles",
            "Verifica que tengas configurado tu codigo de afiliado. "
            "Si dice 'No tenes codigo de afiliado configurado', pedile al admin que lo cargue "
            "en tu usuario. El codigo tiene formato tipo P047071."
        ),
        (
            "Al importar el informe, no aparece ningun cliente",
            "Asegurate de que el codigo de afiliado coincida exactamente con la columna 'Afiliado' "
            "del informe. NyPer filtra la hoja INFO_CARTERA por ese codigo."
        ),
        (
            "Quiero contactar un prospecto pero aparece con candado",
            "Otro gestor ya lo tomo. Comunicate con el o pedile al admin que te lo reasigne "
            "desde el panel de administracion."
        ),
        (
            "Se me cerro la sesion al actualizar la pagina",
            "Normalmente la sesion persiste entre recargas. Si se cerro, puede ser que el token "
            "haya expirado o se haya limpiado el almacenamiento. Volve a loguearte."
        ),
        (
            "Como paso un prospecto a Mi Cartera",
            "En la ficha del prospecto, cuando el estado es 'Contactado' o 'Interesado', "
            "aparece el boton 'Pasar a Mi Cartera'. Presionalo y el cliente se agrega "
            "automaticamente con todos sus datos."
        ),
        (
            "Que pasa si importo el Informe Roles dos veces",
            "La segunda importacion reemplaza toda la cartera. NyPer te muestra un informe "
            "de diferencias: que clientes son nuevos, cuales salieron, y que criterios cambiaron."
        ),
        (
            "Puedo ver la cartera de otro rol",
            "Solo el administrador puede ver las carteras de otros usuarios usando el selector "
            "'Ver cartera de' en Mi Cartera."
        ),
        (
            "Donde esta el boton de cerrar sesion",
            "Arriba a la derecha, en todas las pantallas."
        ),
    ]

    for pregunta, respuesta in preguntas:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(0, 166, 81)
        pdf.multi_cell(0, 6, f"P: {pregunta}")
        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, f"R: {respuesta}")
        pdf.ln(4)

    # ── Contraportada ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 166, 81)
    pdf.cell(0, 15, "NyPer v4.0", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Inteligencia Comercial Territorial", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Banco Provincia", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, "Desarrollado por Pablo Cuadros", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "@Pablocuadros19", align="C", new_x="LMARGIN", new_y="NEXT")

    # Guardar
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pdf.output(OUT)
    print(f"Manual generado: {OUT}")


if __name__ == "__main__":
    generar()
