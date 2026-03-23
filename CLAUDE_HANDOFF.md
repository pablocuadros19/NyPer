# CLAUDE_HANDOFF — 2026-03-23 ~15:15

## Estado actual
App deployada y funcionando en https://nyper101.streamlit.app — Supabase integrado y operativo. App corre bien.

## Último commit
feat: persistencia en Supabase para deploy en la nube

## Qué se hizo en esta sesión
- Sistema de handoff entre cuentas configurado (CLAUDE.md, scripts/, prompts/)
- Git inicializado, repos NyPer y tablero_nacho creados en GitHub (pablocuadros19)
- Supabase integrado: `services/storage.py` reemplaza archivos JSON locales
- Deploy exitoso en Streamlit Community Cloud — logs confirman HTTP 200/201 con Supabase
- Repo NyPer actualmente **público** en GitHub (sin datos sensibles, claves en Streamlit secrets)

## Archivos tocados recientemente
- `services/storage.py` — módulo nuevo, persistencia en Supabase
- `app.py` — reemplazadas funciones _cargar_config, _guardar_config, cargar_leads, guardar_leads
- `requirements.txt` — agregado `supabase`
- `CLAUDE.md` — agregados comandos CAMBIO DE CUENTA y ARRANCAR
- `scripts/cerrar.sh`, `scripts/abrir.sh`, `prompts/arranque.txt` — sistema de handoff

## Próximo paso concreto
En `app.py` ~línea 1045, dentro del tab Prospectos, eliminar el multiselect de rubro del expander de filtros. Solo debe quedar el filtro de estado. Quitar también `f_rub_pr` de la condición `prospectos_filtrados`. El usuario quiere ver todos los prospectos juntos sin filtrar por rubro.

## Decisiones tomadas — NO revertir
- Supabase usa tabla `nyper_storage` con schema key/value JSONB — no cambiar estructura
- `storage.py` usa `@st.cache_resource` para el cliente Supabase — mantener
- Repo NyPer público es aceptable — datos sensibles están en Streamlit secrets y Supabase, no en el código

## Pendientes
- [ ] Quitar filtro rubro del tab Prospectos (próximo paso concreto arriba)
- [ ] Fix warnings `use_container_width` → reemplazar por `width='stretch'` (menor, no urgente)
- [ ] Evaluar si volver repo a privado (no urgente, no hay datos sensibles en el código)

## Contexto que no está en el código
- App URL: https://nyper101.streamlit.app
- Supabase project ID: vgwcnqxrhcbjhuxtniwa
- GitHub: pablocuadros19/NyPer (main) y pablocuadros19/tablero_nacho (main)
- SUCURSAL_CODIGO en uso: 5155 (Villa Ballester)
- tablero-nacho tiene su propio repo separado pero sigue en la carpeta física c:\PRUEBA 101\tablero-nacho\
