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
| `demo_seed.py` | Idempotent seed: 12 causas, personas, seguimientos, audiencias |
| `classifier.py` | Triage classifier → carril verde/amarillo/rojo |
| `pdf_gen.py` | PDF generation via fpdf2 (latin-1 only, `_USE_TTF=False`) |
| `document_gen.py` | Text-only document generation helpers |
| `data_cordoba.py` | Static data: TIPOS_INFRACCION, UNIDADES, CONDICIONES_SUSPENSION |
| `seguimiento_tab.py` | Compliance tracking UI (post-resolución) |
| `agenda_tab.py` | Hearing scheduler: week view, list, new hearing form |
| `perfil_tab.py` | Person profile view (full case/hearing/seguimiento history) |
| `bienvenida.py` | Welcome screen shown once per session |
| `export_excel.py` | Excel export via openpyxl (causas + seguimientos) |

## Database schema (siatc.db — SQLite)
- `personas` — DNI, name, age, address, phone
- `causas` — case number, foreign keys to persona, triage result, state
- `estados_causa` — state transition timeline
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

## Known issues / decisions
- `demo_seed.py → ya_poblado()` checks `n >= 5` (not `>= 12`), so adding
  more seed rows does NOT re-trigger seeding; delete `siatc.db` to reseed.
- `stats_audiencias()` counts by state from the `audiencias` table.
- The `generar_pdf(tipo_doc, caso, clf, fiscal, unidad)` dispatcher in
  `pdf_gen.py` matches on substrings of `tipo_doc` (case-insensitive).
