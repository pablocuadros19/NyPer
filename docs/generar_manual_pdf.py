"""
Genera el manual de usuario de NyPer en PDF (version corta).
Ejecutar: python docs/generar_manual_pdf.py
Salida: docs/Manual_NyPer.pdf
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fpdf import FPDF

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")
OUT = os.path.join(BASE, "docs", "Manual_NyPer.pdf")


class ManualPDF(FPDF):
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

    def titulo(self, num, texto):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 166, 81)
        self.ln(4)
        self.cell(0, 9, f"{num}. {texto}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 166, 81)
        self.line(10, self.get_y(), 70, self.get_y())
        self.ln(3)

    def sub(self, texto):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 30, 46)
        self.ln(2)
        self.cell(0, 7, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def p(self, texto):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, texto)
        self.ln(1.5)

    def item(self, texto):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.cell(6, 5.5, "-")
        self.multi_cell(0, 5.5, texto)
        self.ln(0.5)

    def nota(self, texto):
        self.set_fill_color(240, 249, 244)
        self.set_draw_color(200, 230, 213)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(0, 130, 60)
        self.set_x(10)
        y = self.get_y()
        n_lines = len(self.multi_cell(182, 5, texto, dry_run=True, output="LINES"))
        h = max(12, n_lines * 5 + 4)
        self.rect(10, y, 190, h, style="DF")
        self.set_xy(14, y + 2)
        self.multi_cell(182, 5, texto)
        self.ln(3)


def generar():
    pdf = ManualPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Portada ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(25)
    logo_path = os.path.join(ASSETS, "logo_nyper.png")
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=55, w=100)
        pdf.ln(8)

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(0, 166, 81)
    pdf.cell(0, 16, "NyPer", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Manual de Usuario", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_draw_color(0, 166, 81)
    pdf.line(75, pdf.get_y(), 135, pdf.get_y())
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 7, "Inteligencia Comercial Territorial", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Banco Provincia - v5.0 - Abril 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # ── 1. Acceso ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo("1", "Acceso")
    pdf.p("Abri NyPer en el navegador. Ingresa tu email @bpba.com.ar y la password que te dio el admin. La sesion se mantiene aunque recargues la pagina.")
    pdf.p("Arriba a la derecha: tu nombre y boton Cerrar sesion. Desde cualquier modulo, '<< Inicio' te lleva a la pantalla principal.")

    # ── 2. Pantalla principal ────────────────────────────────────────────────
    pdf.titulo("2", "Pantalla principal")
    pdf.p("Dos opciones:")
    pdf.item("Buscar Clientes: descubrir comercios en tu zona, enriquecerlos y gestionarlos como prospectos.")
    pdf.item("Mi Cartera: tu cartera personal con clientes del Informe Roles y criterios comerciales.")

    # ── 3. Buscar Clientes ───────────────────────────────────────────────────
    pdf.titulo("3", "Buscar Clientes")

    pdf.sub("Descubrir")
    pdf.p("Selecciona tu sucursal arriba. Elegis rubros (obligatorio), radio (max 3 km) y minimo de resenias. Presiona 'Buscar y enriquecer comercios'. En un solo paso NyPer:")
    pdf.item("Busca comercios en Google Places")
    pdf.item("Enriquece con telefono, email y redes sociales")
    pdf.item("Clasifica por canal de contacto y elimina duplicados")
    pdf.p("El perrito aparece mientras trabaja. Los resultados se guardan automaticamente.")

    pdf.sub("Enriquecer (opciones profundas)")
    pdf.p("Para ir mas alla del enriquecimiento basico:")
    pdf.item("Rastrear websites: entra a las paginas web de los comercios buscando emails y redes.")
    pdf.item("Resolver CUITs: cruza con Registro de Sociedades + base LICITARG de proveedores del estado.")
    pdf.item("Consultar ARCA: datos fiscales publicos.")
    pdf.item("Consultar BCRA: situacion crediticia publica.")

    pdf.sub("Bandeja")
    pdf.p("Mapa con pines de colores por canal (verde=WhatsApp, azul=llamada, naranja=mail). Tabla con todos los leads. La columna 'Estado' muestra:")
    pdf.item("Vacio: lead libre, cualquiera puede tomarlo.")
    pdf.item("'Pin Mio': ya es tu prospecto.")
    pdf.item("'Candado + Nombre': ya lo tomo otro gestor, no se puede agregar.")
    pdf.p("Selecciona leads libres en la tabla y presiona 'Agregar a Prospectos'. Se te asignan como gestor automaticamente.")
    pdf.nota("No podes agregar leads que ya fueron tomados por otro gestor.")

    if pdf.get_y() > 200:
        pdf.add_page()

    pdf.sub("Prospectos")
    pdf.p("Tus prospectos en fichas con foto, datos de contacto y links directos (WhatsApp abre chat con mensaje personalizado por rubro, email abre mailto). Cada ficha tiene:")
    pdf.item("Estado: Por contactar / Contactado / Interesado / No interesado")
    pdf.item("Nota libre para registrar observaciones")
    pdf.item("Boton 'Pasar a Mi Cartera' (cuando esta Contactado o Interesado)")
    pdf.item("Boton de campania especial (ej: 'Campania Cuenta DNI' para gastronomia)")
    pdf.p("Por default ves solo tus prospectos. Podes cambiar el filtro a 'Todos' para ver los de la sucursal.")
    pdf.nota("Hay un limite maximo de prospectos por usuario (configurable por el admin). Si llegas al limite, gestionas los que tenes antes de tomar nuevos.")

    pdf.sub("Importar prospectos desde Excel")
    pdf.p("En la pestania Prospectos, despliega 'Importar prospectos desde Excel'. Subi un archivo .xlsx con columnas LOCAL (nombre del comercio) y WHATSAPP (telefono). Se importan como prospectos tuyos, listos para gestionar. Ideal para cargar rutas o listados de campania.")

    pdf.sub("Exportar")
    pdf.p("Descarga Excel completo, por canal, o CSV de campania WhatsApp con links directos. Filtros previos por rubro, zona y calidad.")

    pdf.sub("Analisis")
    pdf.p("Graficos: distribucion por canal, top rubros, tabla por zona, embudo de prospectos.")

    # ── 4. Mi Cartera ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.titulo("4", "Mi Cartera")
    pdf.p("Tu cartera personal. Tres formas de cargar clientes:")

    pdf.sub("Importar Informe Roles (principal)")
    pdf.p("Subi el archivo .xlsb del banco. NyPer filtra por tu codigo de afiliado y carga todos tus clientes con sus 12 criterios comerciales. REEMPLAZA la cartera anterior y muestra un informe de diferencias (clientes nuevos, salientes, criterios que subieron/bajaron).")
    pdf.nota("Necesitas tener tu codigo de afiliado configurado. Si no lo tenes, pedile al admin.")

    pdf.sub("Carga manual")
    pdf.p("Formulario para agregar un cliente a mano: nombre, CUIT, rubro, telefono, email, etc.")

    pdf.sub("Importar Excel generico")
    pdf.p("Subi un .xlsx y se agregan a tu cartera (no reemplaza, suma).")

    pdf.sub("Vista de clientes")
    pdf.p("Cada cliente muestra su scoring de criterios (X/12). Verde = cumple, rojo = no cumple. Podes editar datos y criterios desplegando el cliente.")

    pdf.p("Los 12 criterios: Acreditacion Cupon, ART y Seguros, Descuento Cheques, Haberes, CDNI Comercio, Comex, Emision/Dep. Echeq, Emp. Proveedora, Garantias ON, Inversion Financiera, Pactar, Prestamos Inversion.")

    # ── 5. Ownership ─────────────────────────────────────────────────────────
    pdf.titulo("5", "Gestores")
    pdf.p("Cuando agregas un lead a prospectos, se te asigna como gestor automaticamente. Otro usuario lo ve con candado y no puede tomarlo ni modificarlo. Esto evita que dos roles trabajen sobre el mismo comercio.")
    pdf.p("Solo un admin puede reasignar gestores desde el panel de administracion.")

    # ── 6. Admin ─────────────────────────────────────────────────────────────
    pdf.titulo("6", "Admin (solo administradores)")
    pdf.p("En Buscar Clientes > Inicio > Administracion:")
    pdf.item("Crear usuarios: email @bpba.com.ar, password, rol, color, codigo de afiliado.")
    pdf.item("Activar/desactivar usuarios.")
    pdf.item("Reasignar gestores de prospectos.")
    pdf.item("Configuracion: limite maximo de prospectos por usuario.")
    pdf.p("El admin tambien puede ver la cartera de cualquier usuario en Mi Cartera.")

    # ── Footer ───────────────────────────────────────────────────────────────
    pdf.ln(10)
    pdf.set_draw_color(0, 166, 81)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 7, "NyPer v5.0 - Banco Provincia - Desarrollado por Pablo Cuadros", align="C")

    # Guardar
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pdf.output(OUT)
    print(f"Manual generado: {OUT}")


if __name__ == "__main__":
    generar()
