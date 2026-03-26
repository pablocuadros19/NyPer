# CLAUDE.md — SuperTar

## Qué es SuperTar
App táctica para gestionar campañas de contacto sobre tarjetas pendientes de retiro en sucursal bancaria (Banco Provincia). No reemplaza el sistema TAR — se monta encima del Excel exportado desde TAR para agregar una capa de gestión operativa/comercial.

## Contexto de negocio
- Existe un sistema interno llamado TAR donde se consultan tarjetas (plásticos)
- Desde TAR se exporta un Excel con tarjetas físicamente en sucursal
- Hoy el contacto con clientes para que retiren sus tarjetas se hace de forma manual, lenta y desordenada
- El objetivo es convertir ese trabajo artesanal en una herramienta rápida y accionable
- Cuando se envían mensajes, aumentan los retiros — el problema es la fricción operativa

## Métrica clave
```
tasa de entrega mensual = (entregadas + derivadas) / (stock inicial + ingresos del mes)
```
- "entregadas" y "derivadas" suman positivamente
- "depuradas" no mejoran el ratio igual, pero evitan arrastrar stock inflado
- Promedio del banco: ~35%. Objetivo: ≥40%

## Datos del Excel de TAR
Columnas posibles:
- nombre del cliente
- documento / DNI
- número de tarjeta
- tipo de tarjeta (débito, crédito)
- fecha de recepción / llegada a sucursal
- teléfono
- mail
- estado actual
- otras columnas variables

Importante:
- Cada fila = una tarjeta
- Una persona puede tener varias tarjetas
- Consolidación de tarjetas por cliente: solo si sale fácil y limpio, si no se deja afuera

## Clasificación de contactabilidad
- **Contactables directos:** tienen teléfono y/o mail en el Excel
- **No contactables:** sin teléfono ni mail
- **Potencialmente recuperables:** sin dato en TAR pero posible buscar DNI en otros sistemas internos manualmente

## Canales de contacto
- **WhatsApp:** desde celular de sucursal (no es WhatsApp Business oficial). Hubo baneos previos → los mensajes NO deben ser idénticos, necesitan personalización dinámica por reglas
- **Mail:** apertura de cliente de correo / Outlook
- **Si tiene ambos canales:** sugerir y mostrar ambos, no obligar a elegir uno
- **No hay automatización de envío.** Es contacto asistido: copiar, pegar, enviar manualmente

## Stack
- **Python + Streamlit** como base
- Lectura robusta de Excel (.xlsx) y CSV con pandas/openpyxl
- Exportación CSV/XLSX
- Apertura de WhatsApp Web via URL (`https://wa.me/...`)
- Apertura de mail via `mailto:` con asunto y cuerpo precargados
- Todo local, sin servicios externos
- Sin base de datos compleja — estado en session_state + archivos locales si hace falta

## Arquitectura de carpetas
```
SuperTar/
├── app.py                    # entrada principal Streamlit
├── .streamlit/
│   └── config.toml           # tema Streamlit (colores NyPer)
├── services/
│   ├── file_loader.py        # carga y parseo de Excel/CSV
│   ├── normalizer.py         # normalización de teléfonos, mails, fechas, días de guarda
│   ├── classifier.py         # clasificación por contactabilidad, tipo, antigüedad
│   ├── message_engine.py     # motor de mensajes por reglas
│   ├── campaign_export.py    # exportación de campañas filtradas
│   └── metrics.py            # cálculo de tasa mensual y proyecciones
├── ui/
│   ├── theme.py              # tokens de diseño, CSS centralizado, estilos NyPer
│   ├── components.py         # componentes reutilizables (cards, badges, loader perrito)
│   ├── tab_carga.py          # pantalla de carga de archivo
│   ├── tab_resumen.py        # pantalla de resumen + filtros
│   ├── tab_contacto.py       # pantalla de contacto guiado
│   ├── tab_bandeja.py        # tabla/bandeja filtrable
│   ├── tab_rescate.py        # bandeja de rescate (sin contacto)
│   └── tab_metricas.py       # módulo de tasa mensual
├── assets/
│   ├── logo_nyper.png        # logo NyPer (copiar desde PRUEBA 101)
│   ├── logosolo_clean.png    # ícono NyPer (copiar desde PRUEBA 101)
│   ├── logo_bp.jpg           # logo Banco Provincia (copiar desde PRUEBA 101)
│   ├── perrito_bp.png        # perrito para loader (copiar desde PRUEBA 101)
│   └── perrito_nyp.png       # perrito decorativo (copiar desde PRUEBA 101)
├── data/
│   └── ejemplo_tar.xlsx      # archivo de ejemplo con datos ficticios
├── requirements.txt
├── .env                      # credenciales si las hubiera (nunca commitear)
├── .gitignore
└── CLAUDE.md                 # este archivo
```

## Configuración Streamlit (.streamlit/config.toml)
```toml
[theme]
primaryColor = "#00A651"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f7f9fc"
textColor = "#1a1a2e"
font = "sans serif"
```

## Identidad visual — Sistema de diseño NyPer

### IMPORTANTE: esta app debe sentirse como hermana directa de NyPer
Mismo ecosistema visual, misma familia tipográfica, mismos colores, misma lógica de componentes.

### Paleta de colores
| Token | Valor | Uso |
|---|---|---|
| primary | `#00A651` | botones, accents, headers, gradientes |
| primary-dark | `#00a34d` | hover de botones |
| secondary | `#00B8D4` | gradientes secundarios, accents cyan |
| bg-primary | `#ffffff` | fondo general |
| bg-secondary | `#f7f9fc` | fondo cards, inputs |
| bg-accent | `#f0f9f4` | secciones destacadas (verde muy claro) |
| text-primary | `#1a1a2e` | texto principal |
| text-secondary | `#555555` | texto secundario |
| text-muted | `#666666` | texto tenue |
| text-very-muted | `#999999` | texto muy tenue |
| border-default | `#e0e5ec` | bordes generales |
| border-light | `#d0d5dd` | bordes claros |
| border-green | `#c8e6d5` | bordes verdes suaves |
| tag-bg | `#e8f5ee` | fondo de badges/tags |
| tag-text | `#00A651` | texto de badges/tags |
| hover-bg | `#f0f9f4` | fondo en hover |
| card-hover-shadow | `rgba(0,132,61,.1)` | sombra hover cards |
| btn-hover-shadow | `rgba(0,132,61,.25)` | sombra hover botones |

### Tipografía
- **Fuente:** Montserrat (Google Fonts)
- **Pesos:** 300 (light), 400 (regular), 600 (semibold), 700 (bold), 900 (black)
- **Fallback:** sans-serif

### Tamaños de referencia
| Elemento | Tamaño | Peso |
|---|---|---|
| Hero title | 3.5rem (2rem mobile) | 900 |
| Subtitle | 1rem (0.8rem mobile) | 400, letter-spacing 3px |
| Header title | 1.6rem | 600 |
| Card title (h3) | 1rem (0.9rem mobile) | 700 |
| Card body | 0.85rem | 400, line-height 1.6 |
| Section label | 0.7rem | 700, uppercase, letter-spacing 2px |
| Tags/badges | 0.78rem | 600 |
| Métrica valor | 1.8rem | 700, color #00A651 |
| Métrica label | 0.75rem | uppercase |
| Tabs | 0.9rem | 600 |
| Caption/footer | 0.75rem | — |

### Border radius
| Componente | Radius |
|---|---|
| Cards | 14px |
| Botones | 8px |
| Secciones | 12px |
| Tags/badges | 20px (píldoras) |
| Métricas | 10px |

### Componentes clave

**Botones primarios:**
- Gradient: `linear-gradient(135deg, #00A651, #00a34d)`
- Color texto: blanco
- Font-weight: 600
- Hover: gradient inverso + box-shadow `0 4px 15px rgba(0,132,61,.25)`
- Border-radius: 8px

**Botones secundarios (descarga/acción):**
- Background: blanco
- Color texto: #00A651
- Border: 2px solid #00A651
- Hover: background #f0f9f4

**Cards:**
- Background: #f7f9fc
- Border: 1px solid #e0e5ec
- Border-radius: 14px
- Hover: border-color #00A651, box-shadow 0 4px 20px rgba(0,132,61,.1)

**Secciones destacadas:**
- Background: #f0f9f4
- Border: 1px solid #c8e6d5
- Border-left: 4px solid #00A651
- Border-radius: 12px

**Tabs:**
- Tab list: background blanco, border-bottom 2px #e0e5ec
- Tab activo: color #00A651, border-bottom 3px #00A651
- Tab hover: color #00A651, border-bottom-color #c8e6d5

**Progress bars:**
- Track: #e0e5ec
- Fill: gradient `linear-gradient(90deg, #00A651, #00B8D4)`

**Dividers decorativos:**
- Width: 60px, Height: 3px
- Background: gradient `linear-gradient(90deg, #00A651, #00B8D4)`
- Border-radius: 2px

**Header con gradiente:**
- Background: `linear-gradient(90deg, #ffffff 0%, #00A651 25%, #00B8D4 100%)`
- Border-radius: 12px
- Texto blanco con text-shadow: 0 1px 3px rgba(0,0,0,.15)

### Emojis de tabs
- 📂 Carga
- 📊 Resumen
- 📞 Contacto guiado
- 📋 Bandeja
- 🔍 Rescate
- 📈 Métricas

### Loader del perrito olfateando
OBLIGATORIO: en lugar de spinner genérico, usar el perrito como loader en todos los estados de búsqueda/procesamiento.

Animación CSS del perrito:
```css
@keyframes olfatear {
    0%, 100% { transform: translateX(0) rotate(0deg); }
    50% { transform: translateX(15px) rotate(-3deg); }
}
/* Aplicar: animation: olfatear 1.5s ease-in-out infinite; */
```

Dónde usar:
- Al procesar el Excel
- Al aplicar filtros
- Al recalcular campañas
- Al exportar
- En cualquier espera visible

Componente reutilizable, centralizado, profesional, sin infantilizar.

### Responsive
- Breakpoint mobile: 768px
- Reducir tamaños de fuente, padding, gaps
- Cards en flex-direction column

## Funcionalidades MVP

### 1. Header operativo (configuración global de sesión)
Zona fija superior con:
- Nombre del operador
- Sucursal
- Opcionalmente cargo/sector
- Se completa una vez, queda visible, alimenta los mensajes automáticamente
- Ejemplo en mensaje: "Mi nombre es Pablo, de la sucursal Villa Ballester de Banco Provincia."
- Si no están cargados, generar versión fallback sin romper el mensaje

### 2. Carga de archivo
- Subir Excel (.xlsx) y CSV
- Detectar columnas
- Mapeo simple de columnas si el formato cambia
- Validar errores
- Preview del archivo

### 3. Normalización
- Limpiar y normalizar teléfonos (formato argentino para WhatsApp)
- Detectar mails válidos
- Parsear fecha de recepción
- Calcular días de guarda
- Detectar tipo de tarjeta
- Clasificar por disponibilidad de contacto

### 4. Resumen con cards
- Total de registros
- Total con teléfono / mail / ambos / sin contacto
- Total con más de X días de guarda
- Total por tipo de tarjeta
- Promedio de días de guarda
- Cantidad de registros críticos por antigüedad

### 5. Filtros
- Con teléfono / mail / ambos / sin contacto
- Por tipo de tarjeta
- Por rango de días de guarda
- Por antigüedad crítica
- Por nombre / DNI
- Por estado (si la columna existe)

### 6. Exportar campaña
CSV o Excel limpio con:
- nombre, documento, teléfono, mail, tipo de tarjeta
- fecha de recepción, días de guarda
- canal sugerido
- mensaje sugerido WhatsApp y Mail
- estado interno, etiqueta de campaña

### 7. Contacto guiado (núcleo)
Bandeja tipo "copiar y siguiente" — experiencia de maratón de contacto caso por caso.

Cada caso muestra:
- nombre, documento, tipo de tarjeta, fecha de recepción, días de guarda
- teléfono y/o mail
- canal sugerido, urgencia/prioridad
- mensaje sugerido WhatsApp y mensaje sugerido Mail

Botones:
- Copiar mensaje WhatsApp
- Copiar mensaje Mail
- Abrir WhatsApp Web (con número listo)
- Abrir cliente de mail / Outlook (mailto: con asunto y cuerpo)
- Marcar enviado WhatsApp / Mail
- Copiar y siguiente
- Siguiente

### 8. Bandeja de rescate
- Registros sin teléfono ni mail
- Exportar
- Marcar "pendiente de rescate manual"
- Futura carga manual de contacto recuperado por DNI

### 9. Registro mínimo de gestión (estados)
Estados V1:
- pendiente
- enviado WhatsApp
- enviado Mail
- enviado ambos
- sin contacto
- rescate manual

### 10. Módulo de métricas mensuales
Inputs manuales:
- stock inicial, ingresos, entregadas, derivadas, depuradas

Cálculos:
- tasa actual
- cuánto falta para 40%
- proyección simple
- advertencia si arrastre alto

## Lógica de mensajes

### Reglas por antigüedad (días de guarda)
| Banda | Tono |
|---|---|
| 0-10 días | Informativo suave |
| 11-30 días | Recordatorio moderado |
| 31-45 días | Urgencia mayor |
| 46-60+ días | Prioridad alta |

### Reglas por tipo de tarjeta
- **Débito:** mención suave de que sirve para operar/comprar/cobrar
- **Crédito:** mención suave de promociones/financiación
- **Premium (si se detecta):** tono más sobrio, sin inventar beneficios

### Personalización del mensaje
Incluir cuando está disponible:
- nombre del cliente (si está limpio)
- fecha de recepción
- tipo de tarjeta
- urgencia implícita según días
- nombre del operador (del header)
- sucursal (del header)

NO incluir:
- número completo de tarjeta
- datos sensibles
- promesas exageradas
- lenguaje invasivo

### Firma del operador en mensajes
- "Mi nombre es [NOMBRE_OPERADOR], de la sucursal [SUCURSAL] de Banco Provincia."
- Si faltan datos del operador, fallback sin romper el mensaje

### Dirección / derivación (solo arquitectura futura)
Dejar prevista la lógica pero NO implementar en V1.
Redacción futura posible: "Si te resultara más práctico retirarla en otra sucursal, podemos orientarte sobre cómo gestionarlo."

## Cosas que NO van en la V1
- Automatización de envío de WhatsApp
- Bots automáticos
- WhatsApp Business API
- Respuestas automáticas
- Selector de tono complejo
- Variantes rápidas en pantalla
- FAQ / respuestas frecuentes
- Consolidación compleja de tarjetas por cliente
- Login
- Base de datos compleja
- Integración directa con sistemas bancarios
- Cross-selling fuerte en primer mensaje

## Seguridad
- Diseñar y probar con datos ficticios/anonimizados
- No subir datos reales a servicios externos
- No hardcodear información sensible
- App para entorno local o controlado
- Máximo cuidado con datos — contexto bancario

## Preferencias de código
- Python, snake_case, funciones cortas, código limpio
- Sin clases innecesarias
- Comentarios en español solo cuando aclaran algo no obvio
- Credenciales en `.env`
- MVP primero, iterar rápido
- Sin overengineering ni abstracciones prematuras

## Assets a copiar desde PRUEBA 101
Copiar estos archivos a `SuperTar/assets/`:
- `logo_nyper.png`
- `logosolo_clean.png`
- `logo_bp.jpg`
- `perrito_bp.png`
- `perrito_nyp.png`
- `firma_pablo.png` (opcional, para footer)

## Cómo arrancar
```bash
cd SuperTar
pip install -r requirements.txt
streamlit run app.py
```

## Regla final
> Todo lo que se construya debe cumplir al menos uno:
> **Generar ingresos · Ahorrar tiempo · Mostrar valor profesional**
> Si no cumple → no hacerlo.
