# SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional

Prototipo funcional para el Ministerio Público Fiscal de la Provincia de Córdoba.

## ¿Qué hace?

Clasifica automáticamente causas contravencionales en tres carriles de resolución y genera los documentos legales correspondientes (dictámenes, citaciones), reduciendo el trabajo repetitivo del fiscal o ayudante fiscal.

| Carril | Condición | Acción |
|--------|-----------|--------|
| 🟢 Verde | Primer infractor, conflicto vecinal | Derivación automática a mediación |
| 🟡 Amarillo | Infracción leve, antecedentes menores | Dictamen de suspensión a prueba |
| 🔴 Rojo | Reincidente, daño concreto | Atención fiscal plena |

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Marco legal

- Ley Provincial N° 10.326 — Código de Convivencia Ciudadana de Córdoba
- Ley Provincial N° 10.543 — Mediación como instancia prejudicial
- Ley Provincial N° 7.826 — Ley Orgánica del Ministerio Público Fiscal
