# SIATC — Codebase Guide for Claude

## What this is
SIATC (Sistema Inteligente de Apoyo al Trabajo Contravencional) is a Streamlit
prototype for the Ministerio Público Fiscal de Córdoba, Argentina.
It handles contravention case triage, follow-up tracking, hearing scheduling,
and document generation under Ley Provincial N° 10.326 (CCC).

## How to run
```
cd "E:\Mi unidad\IA\contravencional\prototipo"
python -m streamlit run app.py --server.port 8502
```
App auto-seeds the DB on first launch (no manual step needed).
Reset demo data via Panel de Control > Opciones de demostración.

## Architecture

| File | Purpose |
|---|---|
| `app.py` | Main entry point, 7-tab Streamlit layout |
| `database.py` | All SQLite CRUD via `get_conn()` context manager |
| `demo_seed.py` | Idempotent seed: 15 causas, 14 personas, seguimientos, audiencias |
| `classifier.py` | Triage classifier → carril verde/amarillo/rojo |
| `pdf_gen.py` | PDF generation via fpdf2 (latin-1 only, `_USE_TTF=False`) |
| `document_gen.py` | Text-only document generation helpers |
| `data_cordoba.py` | Static data: TIPOS_INFRACCION (22 types), UNIDADES, CONDICIONES_SUSPENSION |
| `seguimiento_tab.py` | Compliance tracking UI (post-resolución) |
| `agenda_tab.py` | Hearing scheduler: week view, list, new hearing form |
| `perfil_tab.py` | Person profile view (full case/hearing/seguimiento history) |
| `bienvenida.py` | Welcome screen shown once per session (uses real DB stats) |
| `export_excel.py` | Excel export via openpyxl (causas + seguimientos + audiencias) |

## Database schema (siatc.db — SQLite)
- `personas` — DNI, name, age, address, phone
- `causas` — case number, foreign keys to persona, triage result, state, fecha_hecho
- `estados_causa` — state transition timeline (also stores notas when anterior==nuevo)
- `documentos` — generated documents metadata
- `seguimientos` — post-resolution compliance periods
- `condiciones` — individual conditions per seguimiento
- `registros_cumplimiento` — compliance progress entries
- `audiencias` — hearing schedule linked to causas

Foreign keys are ON (`PRAGMA foreign_keys = ON` in `get_conn()`).

## Critical PDF constraints
fpdf2 uses Helvetica (core font, latin-1 charset). Python 3.14 + fonttools
crash when TTF fonts are loaded. Two invariants that MUST be maintained:

1. `_USE_TTF = False` in `pdf_gen.py` — never change this.
2. All text must pass through `_s(text)` before reaching fpdf2. The helper
   class methods (`SiatcPdf.seccion()`, `.titulo_documento()`, etc.) apply
   `_s()` internally, so callers don't need to.
3. `pdf.seccion(titulo, cuerpo)` requires BOTH arguments — calling with only
   `titulo` causes `TypeError: missing 1 required positional argument: 'cuerpo'`.

## Widget key uniqueness (Streamlit)
Duplicate keys crash Streamlit. Pattern used in `seguimiento_tab.py`:
```python
# sid = seguimiento_id, ci = condition index in loop
key=f"s{sid}_est_{ci}"   # NOT f"est_{cond['id']}"
```
Any new widget inside a loop must include at least two disambiguating values.

## Triage / Carril system
- **Verde** → mediación (score < 1.5)
- **Amarillo** → suspensión a prueba (score 1.5–3.0)
- **Rojo** → proceso contravencional pleno (score > 3.0)

## Adding a new tab
1. Add a module `mi_tab.py` with a `render_tab_mi(fiscal)` function.
2. Import it in `app.py`.
3. Add the tab label to the `st.tabs([...])` call.
4. Add `with tab_mi: render_tab_mi(fiscal_nombre)`.

## Adding a new DB table
1. Add CREATE TABLE in `database.py → init_db()`.
2. Add CRUD functions using `with get_conn() as conn:`.
3. Seed sample rows in `demo_seed.py → poblar()` after causas are inserted
   (causas must exist before referencing them via FK).

## Deployment
Target: Streamlit Community Cloud (share.streamlit.io).
Repo: https://github.com/juanfiosa/siatc-cordoba
Requires OAuth in browser — cannot be done headlessly.
`siatc.db` is in `.gitignore`; the cloud instance seeds fresh on each cold start.
`requirements.txt` lists all dependencies.

## Key DB query functions

| Function | Returns |
|---|---|
| `stats_generales()` | total, por_carril, por_estado, por_unidad, personas, reincidentes |
| `causas_por_tipo()` | list of {tipo_infraccion, n} ordered by count |
| `causas_por_mes(meses)` | list of {mes, n} last N months |
| `causas_por_fiscal()` | list of {fiscal_asignado, n} ordered by count |
| `stats_tiempos_resolucion()` | {carril: {dias_promedio, tradicional, reduccion_pct, n}} |
| `causas_inactivas(dias, estados)` | causas in active states with no update in N days |
| `stats_seguimiento()` | total, activos, cumplidos, incumplidos, vencidos |
| `stats_audiencias()` | total, proximas, hoy, realizadas, ausentes |
| `perfil_persona(id)` | {persona, causas, seguimientos, audiencias, antecedentes, total_causas} |
| `listar_causas(estado, carril, unidad, busqueda, tipo_infraccion, fecha_desde, fecha_hasta, limit)` | rows include persona_edad, domicilio, telefono |
| `causas_similares(tipo_infraccion, exclude_persona_id, limit)` | causas of same type excluding a given persona |
| `causas_sin_audiencia_programada(estados)` | causas in active states with no upcoming programada audiencia |
| `causas_count_por_persona(persona_ids)` | bulk dict {persona_id: total_causas} — single query for reincidente badge |
| `causas_mes_actual_vs_anterior()` | {actual, anterior, delta, pct_cambio} — MoM comparison |
| `personas_reincidentes(min_causas)` | personas with ≥ min_causas, with carriles and estados |
| `agregar_nota_causa(causa_id, nota, usuario)` | insert note into estados_causa (anterior==nuevo), touch updated_at |
| `actividad_reciente(limit)` | global feed joining estados_causa + causas + personas |
| `stats_edad()` | {bucket: count} for 5 age groups (16-25, 26-35, 36-45, 46-55, 56+) |
| `stats_edad_por_carril()` | cross-tab: {bucket: {verde, amarillo, rojo}} counts of causas |
| `stats_por_fiscal()` | list of {fiscal_asignado, total, resueltas, pct_resolucion, pct_no_punitivo, dias_promedio, no_punitivas} |

## PDF functions (pdf_gen.py)

| Function | Description |
|---|---|
| `pdf_dictamen_mediacion(caso, clf, fiscal, unidad)` | Dictamen derivación a mediación |
| `pdf_dictamen_suspension(caso, clf, fiscal, unidad)` | Dictamen suspensión a prueba |
| `pdf_citacion(caso, fiscal, unidad, motivo)` | Cédula de notificación/citación |
| `pdf_acta_compromiso(caso, condiciones, fiscal, unidad)` | Acta de compromiso |
| `pdf_informe_incumplimiento(caso, seg, conds_inc, fiscal, unidad)` | Informe incumplimiento |
| `pdf_informe_seguimiento(seg, condiciones, prog, fiscal, unidad)` | Informe de avance del seguimiento post-resolución |
| `pdf_reporte_diario(stats, auds_hoy, causas_pend, fiscal, unidad)` | Reporte ejecutivo diario |
| `pdf_perfil_persona(perfil, fiscal, unidad)` | Ficha institucional del imputado/a |
| `pdf_requerimiento_apertura(caso, clf, fiscal, unidad)` | Requerimiento Fiscal de Apertura del Proceso |
| `generar_pdf(tipo_doc, caso, clf, fiscal, unidad)` | Dispatcher — matches tipo_doc substrings |

## document_gen.py functions

| Function | Description |
|---|---|
| `generar_dictamen_mediacion(caso, clf, fiscal, unidad_key)` | Text dictamen mediación |
| `generar_dictamen_suspension(caso, clf, fiscal, unidad_key)` | Text dictamen suspensión |
| `generar_citacion(caso, fiscal, unidad_key, motivo)` | Text cédula de notificación |
| `generar_requerimiento_apertura(caso, clf, fiscal, unidad_key)` | Text requerimiento apertura |
| `generar_resumen_ejecutivo(caso, clasificacion)` | Text resumen del triaje |

## CONDICIONES_SUSPENSION categories (data_cordoba.py)
`transito`, `transito_alcoholemia`, `convivencia`, `comercio`, `integridad`, `espacio_publico`
— all `_get_condiciones()` helpers in pdf_gen.py, document_gen.py, seguimiento_tab.py
must handle all six categories.

## TIPOS_INFRACCION categories (data_cordoba.py)
22 types across 5 categories:
- **Tránsito**: sin_documentacion, sin_casco, alcoholemia, exceso_velocidad, semaforo, uso_celular, estacionamiento, contramano
- **Convivencia**: ruidos_molestos_nocturnos, ruidos_molestos_diurnos, animales_sueltos, obstruccion_espacio_publico, riña_verbal_vecinal, abandono_animales
- **Comercio**: establecimiento_ruidos, establecimiento_horario, venta_ambulante_sin_habilitacion
- **Espacio Público**: consumo_alcohol_via_publica, deterioro_bienes_publicos, quema_residuos
- **Integridad**: amenazas_leves, agresion_fisica_leve, acoso_callejero

## Panel de Control features
- Distribución por carril (pie chart)
- **Causas por categoría** (pie + table): Tránsito / Convivencia / Comercio / Integridad / Espacio Público
- Infracciones más frecuentes (bar chart)
- Causas por estado / por unidad (bar charts)
- Causas por mes — evolución temporal (bar + line)
- Causas por fiscal (horizontal bar)
- **Tiempos de resolución** vs. proceso tradicional (grouped bar) — uses `stats_tiempos_resolucion()`
- **Mes actual vs. anterior** banner (warning/success/info)
- **Resumen ejecutivo automático** collapsible — natural language bullet-point status
- KPIs: tasa comparecencia, resolver sin condena %, resueltas %, archivadas
- **Perfil demográfico**: age distribution bar chart + stacked carril-by-age chart
- Seguimientos: estado pie + tabla activos con días restantes
- Audiencias: estado pie + tabla próximas
- **Causas sin audiencia programada** — dataframe of causas with no upcoming audiencia
- **Reincidencia**: metrics + table of personas with ≥2 causas
- **Causas sin actividad reciente** — configurable threshold (7/14/30/60 días)
- **Rendimiento por fiscal** table — total, resueltas, pct_resolucion, pct_no_punitivo, dias_promedio (ProgressColumn)
- Exportación Excel: causas+personas+estadísticas+por_fiscal, seguimientos, audiencias, reporte diario PDF

## Gestión de Causas filters (app.py Tab 2)
- Row 1: busqueda (text), estado, carril, unidad
- Row 2 (collapsible): tipo_infraccion selectbox + fecha_desde / fecha_hasta date inputs + "Limpiar" button
- All filters wired to `listar_causas()`; clear resets session_state keys and reruns
- Tipo infracción info card shown below selectbox in Nuevo Caso (articulo, categoria, gravedad, vecinal)
- Tabla view shows "Sin mov. (días)" NumberColumn for active cases; includes CSV export button
- **Quick-stats banner**: 6-metric row (Total, Activas, Resueltas, Verde/Amarillo/Rojo) shown for current filter
- **Reincidente badge**: expander header shows ⚠️ Rein. when persona has >1 causa (bulk lookup via `causas_count_por_persona()`)
- **Siguiente paso sugerido**: `st.caption` inside each expander with contextual next-action hint based on estado+carril
  - ingresada → triage; clasificada verde → citación mediación; clasificada amarillo → citación suspensión;
    clasificada rojo → requerimiento apertura; notificada → programar audiencia;
    en_mediacion → suscribir acta; resuelta → verificar seguimiento (auto-checks via `get_seguimiento_por_causa`)

## Cached DB wrappers (app.py — TTL=60s)
```python
_c_stats_generales()       # wraps stats_generales()
_c_stats_seguimiento()     # wraps stats_seguimiento()
_c_stats_audiencias()      # wraps stats_audiencias()
_c_sin_audiencia()         # wraps causas_sin_audiencia_programada()
_c_stats_por_fiscal()      # wraps stats_por_fiscal()
_c_sin_seguimiento()       # wraps causas_sin_seguimiento()
```
All mutation sites call `st.cache_data.clear()` before `st.rerun()`.

## App-level alerts (app.py)
After the main header, before tabs, SIATC shows warning banners for:
- Audiencias programadas HOY
- Seguimientos vencidos sin cierre
- Seguimientos incumplidos
- Incomparecencias en los últimos 7 días
- Causas notificadas/clasificadas sin audiencia programada

## Gestión de Causas (app.py Tab 2)
Each causa expander shows:
- DNI | Unidad | Fiscal (row 1)
- 📞 Tel. | 🏠 Dom. (row 2, from persona_telefono / persona_domicilio)
- Descripción, Fecha del hecho, Fecha ingresada
- **Timeline**: state transitions AND notes (📝 icon, grey border when anterior==nuevo)
- **Nota rápida** popover: free-text note saved without state change
- Audiencia popover: schedule hearing from within causa
- Documento generator: per-carril options including Requerimiento apertura for rojo
- Vista Tabla toggle: compact dataframe view vs. full detail expanders

## Nuevo Caso (app.py Tab 1)
Form fields: DNI (auto-lookup with format validation), nombre, edad, domicilio,
**teléfono** (3-col layout), tipo infracción, descripción, fecha_hecho,
víctima/lesiones/resistencia checkboxes.
Name-based fallback search: expander with text input → selectbox → "Usar esta persona".
All person data (including telefono) saved via `upsert_persona()`.
DNI validation: warns on non-digit chars, <7 digits, >9 digits.

## Agenda (agenda_tab.py)
On audiencia state change:
- **ausente**: auto-insert INCOMPARECENCIA nota in causa timeline with date + hearing type
- **realizada**: auto-insert confirmation nota with optional observation
Both use `agregar_nota_causa()` for the audit trail.

## Seguimiento (seguimiento_tab.py)
- Auto-suggest close banner when all conditions are `cumplido`
- Error banner when conditions are `incumplido`
- Close button becomes primary (blue) when all conditions met
- On close (cumplido/incumplido/revocado): auto-insert causa timeline note
- **Informe PDF** download button per seguimiento (uses `pdf_informe_seguimiento()`)

## Perfil (perfil_tab.py)
- Visual Gantt timeline (px.timeline) showing causas/seguimientos/audiencias over time
- "Causas similares" expander per infraction type (uses `causas_similares()`)
- Editable contact form (nombre, edad, domicilio, teléfono) via `upsert_persona()`

## Known issues / decisions
- `demo_seed.py → ya_poblado()` checks `n >= 5` (not `>= 15`), so adding
  more seed rows does NOT re-trigger seeding; delete `siatc.db` to reseed.
- `stats_audiencias()` counts by state from the `audiencias` table.
- `generar_pdf(tipo_doc, caso, clf, fiscal, unidad)` dispatcher matches on
  substrings of `tipo_doc` (case-insensitive).
- `get_seguimiento_por_causa` and `get_condiciones` must be explicitly imported
  in app.py (not via `db.` prefix — there is no `import database as db` there).
- Reset demo data in Panel de Control deletes siatc.db then calls init_db()+poblar().
  If Streamlit holds the file, deletion may fail silently. Workaround: stop the
  server, delete manually, restart.
- The `_nuevo_persona_override` session_state pattern in Nuevo Caso uses
  `st.rerun()` to apply the selected person; on rerun the override key is
  popped from session_state and applied before form rendering.

## Demo seed state (15 causas, 14 personas)
- Garcia (idx 0): 2 causas (transito_sin_doc archivada + transito_exceso_vel clasificada) → reincidente
- Personas idx 12 (Villareal) y 13 (Acuña): Unidad Género, causas notificada/clasificada,
  updated_at forzado a 35d/20d → aparecen en "Causas sin actividad reciente"
- Acuña (idx 13): sin audiencia programada → aparece en "Causas sin audiencia programada"
- Martinez (idx 4): notificada, updated_dias=8 → aparece en umbral 7d
