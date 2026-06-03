-- ============================================================
-- SIATC: Integración Contravencional en Supabase
-- Sistema Inteligente de Apoyo al Trabajo Contravencional
-- MPF Córdoba — Ley N° 10.326 (CCC)
--
-- INSTRUCCIONES:
--   Ejecutar en el SQL Editor de Supabase del proyecto sumarios-rc.
--   Este archivo extiende la tabla 'causas' existente con campos CCC
--   y crea las tablas específicas del proceso contravencional.
--
-- PRECONDICIÓN: el schema.sql de sumarios-rc debe estar aplicado.
-- ============================================================

-- ── 1. Extensión de la tabla causas con campos CCC ────────────────────────────
-- Estos campos solo aplican cuando tipo_causa = 'contravencional'

ALTER TABLE causas
  ADD COLUMN IF NOT EXISTS carril              TEXT CHECK (carril IN ('verde','amarillo','rojo')),
  ADD COLUMN IF NOT EXISTS score_ccc           FLOAT,
  ADD COLUMN IF NOT EXISTS accion_ccc          TEXT,
  ADD COLUMN IF NOT EXISTS fundamento_ccc      TEXT[],
  ADD COLUMN IF NOT EXISTS victima_ccc         BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS lesiones_ccc        BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS resistencia_ccc     BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS fiscal_nombre_ccc   TEXT,  -- nombre del fiscal (puede diferir de magistrado)
  ADD COLUMN IF NOT EXISTS tipo_infraccion_ccc TEXT,  -- clave del catálogo TIPOS_INFRACCION
  ADD COLUMN IF NOT EXISTS oficina_actual_ccc  TEXT DEFAULT 'fiscalia', -- tenencia actual en SIATC
  ADD COLUMN IF NOT EXISTS tipo_proceso_ccc    TEXT DEFAULT 'contravencional';  -- contravencional / penal

COMMENT ON COLUMN causas.carril             IS 'SIATC: resultado del triaje CCC (verde/amarillo/rojo)';
COMMENT ON COLUMN causas.score_ccc          IS 'SIATC: score numérico del clasificador';
COMMENT ON COLUMN causas.tipo_infraccion_ccc IS 'SIATC: clave del catálogo CCC (ej: transito_alcoholemia)';
COMMENT ON COLUMN causas.oficina_actual_ccc  IS 'SIATC: oficina MPF que tiene la tenencia';

-- ── 2. Seguimientos post-resolución ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS seguimientos_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id        UUID NOT NULL REFERENCES causas(id) ON DELETE CASCADE,
  tipo_resolucion TEXT NOT NULL,   -- suspension | mediacion | acuerdo
  fecha_inicio    DATE NOT NULL,
  fecha_fin       DATE NOT NULL,
  estado          TEXT NOT NULL DEFAULT 'activo',  -- activo | cumplido | incumplido | revocado
  fiscal          TEXT,
  observaciones   TEXT,
  proximo_control DATE,            -- próxima fecha de control agendada
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 3. Condiciones del seguimiento ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS condiciones_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  seguimiento_id  UUID NOT NULL REFERENCES seguimientos_ccc(id) ON DELETE CASCADE,
  tipo            TEXT NOT NULL,   -- trabajo_comunitario | curso | multa | prohibicion | otro
  descripcion     TEXT NOT NULL,
  valor_objetivo  FLOAT DEFAULT 0,
  unidad          TEXT DEFAULT '',  -- horas | pesos | controles | sesiones
  estado          TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente | en_curso | cumplido | incumplido
  fecha_limite    DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 4. Registros de cumplimiento (avance en condiciones cuantitativas) ────────
CREATE TABLE IF NOT EXISTS registros_cumplimiento_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  condicion_id    UUID NOT NULL REFERENCES condiciones_ccc(id) ON DELETE CASCADE,
  fecha           DATE NOT NULL,
  valor_parcial   FLOAT NOT NULL DEFAULT 0,
  observaciones   TEXT,
  registrado_por  TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 5. Audiencias CCC ────────────────────────────────────────────────────────
-- Diferente de la agenda policial; son las audiencias fiscales CCC
CREATE TABLE IF NOT EXISTS audiencias_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id        UUID NOT NULL REFERENCES causas(id) ON DELETE CASCADE,
  tipo            TEXT NOT NULL DEFAULT 'audiencia',
  --   audiencia | mediacion | acta_compromiso | control_seg
  fecha           DATE NOT NULL,
  hora            TIME NOT NULL DEFAULT '09:00',
  lugar           TEXT DEFAULT '',
  estado          TEXT NOT NULL DEFAULT 'programada',
  --   programada | realizada | ausente | reprogramada | cancelada
  observaciones   TEXT DEFAULT '',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 6. Documentos CCC generados por SIATC ────────────────────────────────────
CREATE TABLE IF NOT EXISTS documentos_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id        UUID NOT NULL REFERENCES causas(id) ON DELETE CASCADE,
  tipo_documento  TEXT NOT NULL,
  contenido       TEXT,           -- texto del documento generado
  generado_por    TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 7. Historial de estados CCC (audit trail del proceso fiscal) ──────────────
CREATE TABLE IF NOT EXISTS estados_causa_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id        UUID NOT NULL REFERENCES causas(id) ON DELETE CASCADE,
  estado_anterior TEXT,
  estado_nuevo    TEXT NOT NULL,
  usuario         TEXT NOT NULL DEFAULT '',
  observaciones   TEXT DEFAULT '',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 8. Mensajería inter-oficina CCC ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mensajes_ccc (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id         UUID REFERENCES causas(id),
  tipo             TEXT NOT NULL,   -- notificacion | instruccion | consulta | respuesta | resolucion
  asunto           TEXT NOT NULL,
  cuerpo           TEXT DEFAULT '',
  oficina_origen   TEXT NOT NULL,
  usuario_origen   TEXT DEFAULT '',
  oficina_destino  TEXT NOT NULL,
  estado           TEXT DEFAULT 'enviado',  -- enviado | recibido | procesado
  prioridad        TEXT DEFAULT 'normal',   -- normal | urgente
  adjunto_tipo     TEXT DEFAULT '',
  referencia_id    UUID REFERENCES mensajes_ccc(id),  -- threading
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  leido_at         TIMESTAMPTZ
);

-- ── 9. Pases de expediente entre oficinas ────────────────────────────────────
CREATE TABLE IF NOT EXISTS pases_ccc (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id         UUID NOT NULL REFERENCES causas(id) ON DELETE CASCADE,
  oficina_origen   TEXT NOT NULL,
  usuario_origen   TEXT DEFAULT '',
  oficina_destino  TEXT NOT NULL,
  motivo           TEXT NOT NULL DEFAULT '',
  observaciones    TEXT DEFAULT '',
  estado           TEXT DEFAULT 'enviado',  -- enviado | recibido | rechazado
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  recibido_at      TIMESTAMPTZ
);

-- ── 10. Notificaciones al imputado ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notificaciones_ccc (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  causa_id        UUID REFERENCES causas(id),
  tipo            TEXT NOT NULL DEFAULT 'email',  -- email | sms | whatsapp
  destinatario    TEXT NOT NULL DEFAULT '',
  asunto          TEXT NOT NULL DEFAULT '',
  cuerpo          TEXT NOT NULL DEFAULT '',
  estado          TEXT NOT NULL DEFAULT 'enviada',  -- pendiente | enviada | error
  enviado_at      TIMESTAMPTZ,
  created_by      TEXT DEFAULT '',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Índices ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_causas_carril
  ON causas(carril) WHERE tipo_causa = 'contravencional';

CREATE INDEX IF NOT EXISTS idx_causas_tipo_infraccion
  ON causas(tipo_infraccion_ccc) WHERE tipo_causa = 'contravencional';

CREATE INDEX IF NOT EXISTS idx_causas_oficina_ccc
  ON causas(oficina_actual_ccc) WHERE tipo_causa = 'contravencional';

CREATE INDEX IF NOT EXISTS idx_seguimientos_causa   ON seguimientos_ccc(causa_id);
CREATE INDEX IF NOT EXISTS idx_condiciones_seg      ON condiciones_ccc(seguimiento_id);
CREATE INDEX IF NOT EXISTS idx_registros_cond       ON registros_cumplimiento_ccc(condicion_id);
CREATE INDEX IF NOT EXISTS idx_audiencias_causa_ccc ON audiencias_ccc(causa_id);
CREATE INDEX IF NOT EXISTS idx_audiencias_fecha_ccc ON audiencias_ccc(fecha);
CREATE INDEX IF NOT EXISTS idx_documentos_causa_ccc ON documentos_ccc(causa_id);
CREATE INDEX IF NOT EXISTS idx_estados_ccc_causa    ON estados_causa_ccc(causa_id);
CREATE INDEX IF NOT EXISTS idx_mensajes_ccc_causa   ON mensajes_ccc(causa_id);
CREATE INDEX IF NOT EXISTS idx_mensajes_ccc_destino ON mensajes_ccc(oficina_destino);
CREATE INDEX IF NOT EXISTS idx_pases_ccc_causa      ON pases_ccc(causa_id);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE seguimientos_ccc        ENABLE ROW LEVEL SECURITY;
ALTER TABLE condiciones_ccc         ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros_cumplimiento_ccc ENABLE ROW LEVEL SECURITY;
ALTER TABLE audiencias_ccc          ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos_ccc          ENABLE ROW LEVEL SECURITY;
ALTER TABLE estados_causa_ccc       ENABLE ROW LEVEL SECURITY;
ALTER TABLE mensajes_ccc            ENABLE ROW LEVEL SECURITY;
ALTER TABLE pases_ccc               ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificaciones_ccc      ENABLE ROW LEVEL SECURITY;

-- Acceso a través de causas (hereda la política de causas)
CREATE POLICY "seguimientos_via_causa" ON seguimientos_ccc
  FOR ALL USING (causa_id IN (SELECT id FROM causas));

CREATE POLICY "condiciones_via_seg" ON condiciones_ccc
  FOR ALL USING (seguimiento_id IN (SELECT id FROM seguimientos_ccc));

CREATE POLICY "registros_via_cond" ON registros_cumplimiento_ccc
  FOR ALL USING (condicion_id IN (SELECT id FROM condiciones_ccc));

CREATE POLICY "audiencias_via_causa" ON audiencias_ccc
  FOR ALL USING (causa_id IN (SELECT id FROM causas));

CREATE POLICY "documentos_via_causa" ON documentos_ccc
  FOR ALL USING (causa_id IN (SELECT id FROM causas));

CREATE POLICY "estados_ccc_via_causa" ON estados_causa_ccc
  FOR ALL USING (causa_id IN (SELECT id FROM causas));

CREATE POLICY "pases_via_causa" ON pases_ccc
  FOR ALL USING (causa_id IN (SELECT id FROM causas));

CREATE POLICY "notifs_via_causa" ON notificaciones_ccc
  FOR ALL USING (causa_id IN (SELECT id FROM causas) OR causa_id IS NULL);

-- Mensajes: cada usuario ve los de su dependencia
CREATE POLICY "mensajes_ccc_acceso" ON mensajes_ccc
  FOR ALL USING (
    causa_id IN (SELECT id FROM causas)
    OR causa_id IS NULL
  );

-- ── Trigger: updated_at en seguimientos ──────────────────────────────────────
CREATE TRIGGER trg_seguimientos_ccc_updated_at
  BEFORE UPDATE ON seguimientos_ccc
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Vista: causas contravencionales con estado SIATC ─────────────────────────
CREATE OR REPLACE VIEW v_causas_contravencionales AS
SELECT
  c.id,
  c.numero,
  c.anio,
  c.caratula,
  c.descripcion_hecho,
  c.fecha_hecho,
  c.hora_hecho,
  c.lugar_hecho,
  c.estado                  AS estado_policial,
  c.carril,
  c.score_ccc,
  c.accion_ccc,
  c.tipo_infraccion_ccc,
  c.victima_ccc,
  c.lesiones_ccc,
  c.resistencia_ccc,
  c.fiscal_nombre_ccc,
  c.oficina_actual_ccc,
  c.dependencia_id,
  c.sumariante_id,
  c.magistrado_id,
  c.remitido_en,
  c.created_at,
  c.updated_at,
  -- Persona imputada principal (primer imputado de la causa)
  p.apellido || ', ' || p.nombre AS apellido_nombre_imputado,
  p.dni                          AS dni_imputado,
  p.fecha_nac,
  EXTRACT(YEAR FROM AGE(p.fecha_nac))::INT AS edad_imputado,
  p.domicilio                    AS domicilio_imputado,
  p.telefono                     AS telefono_imputado
FROM causas c
LEFT JOIN personas p ON p.causa_id = c.id AND p.rol = 'imputado'
WHERE c.tipo_causa = 'contravencional';

COMMENT ON VIEW v_causas_contravencionales IS
  'Vista unificada de causas contravencionales con datos de imputado. '
  'Usada por SIATC para mostrar causas sin necesidad de múltiples JOINs.';

-- ── Vista: dashboard SIATC por fiscal ────────────────────────────────────────
CREATE OR REPLACE VIEW v_siatc_dashboard AS
SELECT
  c.fiscal_nombre_ccc                                   AS fiscal,
  COUNT(*) FILTER (WHERE c.carril = 'verde')            AS verde,
  COUNT(*) FILTER (WHERE c.carril = 'amarillo')         AS amarillo,
  COUNT(*) FILTER (WHERE c.carril = 'rojo')             AS rojo,
  COUNT(*) FILTER (WHERE c.estado = 'en_tramite')       AS activas,
  COUNT(*) FILTER (WHERE c.estado = 'remitido'
                   AND c.carril IS NULL)                AS pendientes_triaje,
  COUNT(*)                                              AS total
FROM causas c
WHERE c.tipo_causa = 'contravencional'
GROUP BY c.fiscal_nombre_ccc;

-- ── Función: crear causa contravencional desde SIATC (inicio fiscal) ──────────
CREATE OR REPLACE FUNCTION crear_causa_contravencional(
  p_numero            TEXT,
  p_caratula          TEXT,
  p_descripcion       TEXT,
  p_fecha_hecho       DATE,
  p_lugar_hecho       TEXT,
  p_tipo_infraccion   TEXT,
  p_dependencia_id    UUID,
  p_fiscal_nombre     TEXT,
  p_imputado_apellido TEXT,
  p_imputado_nombre   TEXT,
  p_imputado_dni      TEXT DEFAULT NULL,
  p_imputado_edad     INT  DEFAULT NULL,
  p_imputado_domicilio TEXT DEFAULT NULL,
  p_imputado_telefono TEXT DEFAULT NULL
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_causa_id UUID;
  v_anio INT := EXTRACT(YEAR FROM NOW())::INT;
BEGIN
  -- Crear la causa
  INSERT INTO causas (
    numero, anio, tipo_causa, tipo_inicio, caratula, descripcion_hecho,
    fecha_hecho, lugar_hecho, estado, dependencia_id,
    tipo_infraccion_ccc, fiscal_nombre_ccc
  ) VALUES (
    p_numero, v_anio, 'contravencional', 'denuncia_formulada',
    p_caratula, p_descripcion, p_fecha_hecho, p_lugar_hecho,
    'en_tramite', p_dependencia_id,
    p_tipo_infraccion, p_fiscal_nombre
  )
  RETURNING id INTO v_causa_id;

  -- Registrar al imputado como persona
  INSERT INTO personas (
    causa_id, rol, apellido, nombre, dni, edad, domicilio, telefono
  ) VALUES (
    v_causa_id, 'imputado',
    p_imputado_apellido, p_imputado_nombre,
    p_imputado_dni, p_imputado_edad,
    p_imputado_domicilio, p_imputado_telefono
  );

  -- Registrar en historial
  INSERT INTO historial_estados (causa_id, estado_nuevo, observacion)
  VALUES (v_causa_id, 'en_tramite', 'Causa ingresada directamente por fiscalía (SIATC)');

  RETURN v_causa_id;
END;
$$;

COMMENT ON FUNCTION crear_causa_contravencional IS
  'Crea una causa contravencional de inicio fiscal (Art. 125 CCC: '
  'acción pública promovida por denuncia ante autoridad competente). '
  'Usado por SIATC cuando el fiscal inicia sin acta policial previa.';
