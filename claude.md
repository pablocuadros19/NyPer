# CLAUDE.md — Contexto de Pablo

## Quién soy
- **Nombre:** Pablo | Argentina
- **Rol:** Empleado bancario (Banco Provincia) — +15 años de experiencia
- **Formación:** Lic. en Administración de Empresas
- **Perfil:** Puente negocio↔tecnología. No soy dev puro.

## Nivel técnico
| Área | Nivel |
|---|---|
| Python | Básico/intermedio |
| APIs REST | Básico |
| Frontend | Muy básico |
| Power BI / datos | Intermedio |
| IA generativa | En crecimiento (foco principal) |
| Infra / DevOps | Inicial |

**Aprendiendo activamente:** Claude Code, agentes, Streamlit, automatización con IA, integraciones reales (WhatsApp, APIs), arquitecturas locales (Mac Mini).

## Mis proyectos

### Banco (Banco Provincia)
Objetivo: generar ventas, activar clientes, mejorar conversión.
- **Banco Mark 1** — agente comercial
- Sistema de tarjetas no retiradas
- Campañas multicanal inteligentes (mail + WhatsApp)

### VIKA (impresión 3D)
- Automatizar catálogo, pricing y publicaciones
- Estandarizar operaciones y branding

### LUMEN (educación + IA)
- Foco en Prácticas del Lenguaje, para docentes
- Generador de prompts educativos, chatbot docente, productos con IA

### Otros
- Agentes locales en Mac Mini
- Productos vendibles con IA

## Cómo trabajar conmigo

### Comunicación
- Español siempre. Inglés técnico solo si suma.
- Directo, sin relleno. Formato ideal: breve explicación → código → próximo paso.

### Autonomía
- **Actuar sin preguntar:** tarea clara, código estándar, sin riesgo.
- **Preguntar antes:** decisiones de arquitectura, datos sensibles, servicios externos reales, cambios que puedan romper algo.

### Filosofía
- MVP primero. Iterar rápido. Validar antes de escalar.
- Rol del agente: mantenerme enfocado y simple cuando yo quiera ir a lo complejo demasiado rápido.

## Stack y entorno
- **OS:** Windows (PC principal) + Mac Mini (servidor de agentes, futuro)
- **Editor:** VS Code + terminal
- **Lenguaje principal:** Python (snake_case, funciones cortas, sin clases innecesarias)
- **Lenguaje secundario:** JavaScript (solo si aporta valor real)
- **Frameworks:** Streamlit, APIs REST, scripts de automatización
- **IA:** Claude Code, Anthropic API, OpenAI API

## Preferencias de código
- Simple > complejo. Legible > ingenioso.
- Sin overengineering, sin abstracciones prematuras, sin dependencias innecesarias.
- Comentarios solo cuando agregan valor real.
- Credenciales siempre en `.env`, nunca hardcodeadas.
- Estructura base: `app.py` + `services/` + `utils/` + `data/`

## Seguridad — NUNCA sin confirmar
- Borrar archivos o sobrescribir código crítico
- Usar o simular datos reales/identificables
- Integrarse con servicios reales (WhatsApp, APIs pagas, etc.)
- Push a main o commits automáticos

**⚠️ Trabajo en banco → máximo cuidado con datos. 

## Regla final
> Todo lo que se construya debe cumplir al menos uno:
> **Generar ingresos · Ahorrar tiempo · Mostrar valor profesional**
> Si no cumple → no hacerlo.

---

## Comandos especiales del sistema de handoff

### Al iniciar cualquier sesión nueva
1. Verificar si existe `CLAUDE_HANDOFF.md` en la raíz del proyecto
2. Si existe y tiene contenido real (no solo el template vacío): leerlo automáticamente
3. Leer también `TASKS.md` sección "En curso"
4. Presentar resumen de 3-4 líneas: qué está en curso, cuál es el próximo paso
5. Esperar confirmación de Pablo antes de tocar cualquier archivo

### Cuando Pablo diga "CAMBIO DE CUENTA"
Ejecutar sin preguntar, en este orden:
1. Escribir/reemplazar `CLAUDE_HANDOFF.md` completo con el estado actual de la sesión
   - Incluir fecha y hora real
   - Incluir el próximo paso como instrucción específica (archivo + línea si aplica)
   - Incluir decisiones tomadas en la sesión que no deben revertirse
2. Ejecutar: `git add . && git commit -m "handoff: [resumen de lo hecho]"`
3. Ejecutar: `git push` (si falla por no haber remote, ignorar y continuar)
4. Avisar con exactamente esto: "Listo. CLAUDE_HANDOFF.md escrito y commit hecho. Podés cerrar sesión."

### Cuando cualquier cuenta diga "ARRANCAR"
Ejecutar sin preguntar, en este orden:
1. Leer `CLAUDE_HANDOFF.md`
2. Leer `TASKS.md`
3. Leer `CLAUDE.md`
4. Presentar resumen en este formato exacto:
   - **En curso:** [qué se estaba haciendo]
   - **Próximo paso:** [instrucción concreta]
   - **No tocar:** [decisiones tomadas que no se revierten]
   - **Pendiente:** [resto de tasks]
5. Preguntar: "¿Arrancamos con esto?" y esperar confirmación antes de tocar cualquier archivo.
