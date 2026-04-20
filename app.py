import streamlit as st
import pandas as pd
import phonenumbers
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from modules.rut import validar_rut
from modules.direcciones import parsear_direccion
from modules.comunas import validar_comuna
from modules.deduplicacion import detectar_duplicados

# ── Configuración ──────────────────────────────────────────────
st.set_page_config(page_title="DatoFiel", page_icon="logo.png", layout="wide")

st.markdown("""
<style>
    .main { padding: 2rem; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; padding: 0.75rem 2rem;
        border-radius: 8px; font-size: 1rem; font-weight: 600; width: 100%;
    }
    .tag { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .tag-auto { background: #1e3a2f; color: #a6e3a1; border: 1px solid #a6e3a1; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────
st.image("logo.png", width=200)
st.markdown("Limpia y normaliza tu base de datos chilena en segundos")
st.divider()

# ── Navegación por pestañas ────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🪪 RUT & Direcciones",
    "📱 Teléfonos", 
    "📧 Emails",
    "📊 RFM Analytics",
    "🩺 Diagnóstico Gratuito"
])

# ══════════════════════════════════════════════════════════════
# PESTAÑA 1 — RUT & Direcciones
# ══════════════════════════════════════════════════════════════
with tab1:
    st.subheader("🪪 Limpieza de RUT, Direcciones y Comunas")

    KEYWORDS = {
        "rut":    ["rut", "run", "identificador", "id_fiscal", "tax_id"],
        "dir":    ["direccion", "dirección", "address", "domicilio", "calle"],
        "comuna": ["comuna", "city", "ciudad", "localidad", "district"],
    }

    def detectar_columna(columnas, tipo):
        columnas_lower = [c.lower().strip() for c in columnas]
        for keyword in KEYWORDS[tipo]:
            for i, col in enumerate(columnas_lower):
                if keyword in col:
                    return columnas[i]
        return columnas[0]

    uploaded = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"], key="up1")

    if uploaded:
        df = pd.read_csv(uploaded) if uploaded.name.endswith('.csv') else pd.read_excel(uploaded)
        st.success(f"✅ {len(df):,} registros cargados")

        with st.expander("👁️ Vista previa", expanded=False):
            st.dataframe(df.head(), use_container_width=True)

        st.divider()
        st.markdown("#### 🗂️ Mapeo de columnas")

        col_rut_det    = detectar_columna(list(df.columns), "rut")
        col_dir_det    = detectar_columna(list(df.columns), "dir")
        col_comuna_det = detectar_columna(list(df.columns), "comuna")

        KEYWORDS_NOMBRE = ["nombre", "name", "razon_social", "cliente", "contacto"]
        col_nombre_det = next(
            (c for c in df.columns if any(k in c.lower() for k in KEYWORDS_NOMBRE)),
            df.columns[0]
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('**RUT** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_rut = st.selectbox("", df.columns, index=list(df.columns).index(col_rut_det), key="rut", label_visibility="collapsed")
        with c2:
            st.markdown('**Dirección** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_dir = st.selectbox("", df.columns, index=list(df.columns).index(col_dir_det), key="dir", label_visibility="collapsed")
        with c3:
            st.markdown('**Comuna** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_comuna = st.selectbox("", df.columns, index=list(df.columns).index(col_comuna_det), key="comuna", label_visibility="collapsed")
        with c4:
            st.markdown('**Nombre** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_nombre = st.selectbox("", df.columns, index=list(df.columns).index(col_nombre_det), key="nombre", label_visibility="collapsed")

        st.divider()

        if st.button("🚀 Limpiar Base de Datos", key="btn1"):
            progress = st.progress(0, text="Validando RUTs...")
            df['rut_validado']     = df[col_rut].apply(lambda x: validar_rut(x)['rut_limpio'])
            df['rut_es_valido']    = df[col_rut].apply(lambda x: validar_rut(x)['valido'])
            progress.progress(25, text="Parseando direcciones...")
            parsed                 = df[col_dir].apply(parsear_direccion)
            df['dir_calle']        = parsed.apply(lambda x: x['calle'])
            df['dir_numero']       = parsed.apply(lambda x: x['numero'])
            df['dir_depto']        = parsed.apply(lambda x: x['depto_oficina'])
            progress.progress(50, text="Corrigiendo comunas...")
            comunas                = df[col_comuna].apply(validar_comuna)
            df['comuna_corregida'] = comunas.apply(lambda x: x['comuna_corregida'])
            df['comuna_valida']    = comunas.apply(lambda x: x['valida'])
            progress.progress(75, text="Detectando duplicados...")
            df = detectar_duplicados(df, col_rut=col_rut, col_nombre=col_nombre)
            progress.progress(100, text="¡Listo!")

            ruts_validos   = int(df['rut_es_valido'].sum())
            ruts_invalidos = len(df) - ruts_validos
            comunas_ok     = int(df['comuna_valida'].sum())
            comunas_fix    = len(df) - comunas_ok
            duplicados     = int(df['es_duplicado'].sum())

            st.divider()
            st.subheader("📊 Resumen")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("✅ RUTs válidos",       ruts_validos)
            m2.metric("❌ RUTs inválidos",     ruts_invalidos)
            m3.metric("🏙️ Comunas correctas",  comunas_ok)
            m4.metric("🔧 Comunas corregidas", comunas_fix)
            m5.metric("🔍 Duplicados",         duplicados)

            columnas_ocultas = ['rut_es_valido', 'dir_calle', 'dir_numero', 'dir_depto', 'comuna_valida', 'duplicado_de']
            df_vista = df.drop(columns=[c for c in columnas_ocultas if c in df.columns])
            st.dataframe(df_vista, use_container_width=True)

            df_limpio = df.drop(columns=[c for c in columnas_ocultas + ['es_duplicado', 'tipo_duplicado'] if c in df.columns])
            df_limpio[col_rut]    = df['rut_validado'].fillna(df[col_rut])
            df_limpio[col_comuna] = df['comuna_corregida'].fillna(df[col_comuna])
            df_limpio = df_limpio.drop(columns=['rut_validado', 'comuna_corregida'], errors='ignore')

            d1, d2 = st.columns(2)
            with d1:
                st.download_button("⬇️ CSV limpio", df_limpio.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                                   "datos_limpios.csv", "text/csv", use_container_width=True, type="primary")
                st.caption("Columnas originales con RUT y comuna corregidos")
            with d2:
                st.download_button("⬇️ CSV completo", df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                                   "datos_completo.csv", "text/csv", use_container_width=True)
                st.caption("Incluye todas las columnas de análisis")

# ══════════════════════════════════════════════════════════════
# PESTAÑA 2 — Teléfonos
# ══════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📱 Normalización de Teléfonos Chilenos")

    def normalizar_telefono(numero) -> dict:
        import re
        numero = str(numero).strip()
        limpio = re.sub(r'[^\d]', '', numero)

        if len(limpio) == 9 and limpio.startswith('9'):
            limpio = '+56' + limpio
        elif len(limpio) == 10 and limpio.startswith('9'):
            limpio = '+56' + limpio
        elif len(limpio) == 11 and limpio.startswith('569'):
            limpio = '+' + limpio
        elif len(limpio) == 11 and limpio.startswith('56'):
            limpio = '+56' + limpio[2:]
        elif len(limpio) == 8 and limpio.startswith('9'):
            limpio = '+569' + limpio
        else:
            limpio = '+56' + limpio

        try:
            parsed = phonenumbers.parse(limpio, "CL")
            valido = phonenumbers.is_possible_number(parsed)
            if valido:
                formateado = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                # Asegurar formato +56 9 XXXX XXXX
                digitos = re.sub(r'[^\d]', '', formateado)
                if len(digitos) == 11 and digitos.startswith('569'):
                    formateado = f"+56 {digitos[2]} {digitos[3:7]} {digitos[7:]}"
            else:
                formateado = None
            return {"valido": valido, "telefono_normalizado": formateado}
        except:
            return {"valido": False, "telefono_normalizado": None}

    uploaded2 = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"], key="up2")

    if uploaded2:
        df2 = pd.read_csv(uploaded2) if uploaded2.name.endswith('.csv') else pd.read_excel(uploaded2)
        st.success(f"✅ {len(df2):,} registros cargados")

        with st.expander("👁️ Vista previa", expanded=False):
            st.dataframe(df2.head(), use_container_width=True)

        KEYWORDS_TEL = ["telefono", "teléfono", "fono", "phone", "celular", "movil", "móvil", "tel"]
        col_tel_det = next(
            (c for c in df2.columns if any(k in c.lower() for k in KEYWORDS_TEL)),
            df2.columns[0]
        )

        st.markdown('**Columna de teléfono** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
        col_tel = st.selectbox("", df2.columns, index=list(df2.columns).index(col_tel_det), key="tel", label_visibility="collapsed")

        if st.button("📱 Normalizar Teléfonos", key="btn2"):
            with st.spinner("Procesando..."):
                resultado       = df2[col_tel].apply(normalizar_telefono)
                df2['telefono_normalizado'] = resultado.apply(lambda x: x['telefono_normalizado'])
                df2['tel_valido']           = resultado.apply(lambda x: x['valido'])

            validos   = int(df2['tel_valido'].sum())
            invalidos = len(df2) - validos

            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("✅ Teléfonos válidos",   validos)
            m2.metric("❌ Teléfonos inválidos", invalidos)
            m3.metric("📊 Total procesados",    len(df2))

            df2_vista = df2.drop(columns=['tel_valido'])
            st.dataframe(df2_vista, use_container_width=True)

            d1, d2 = st.columns(2)
            with d1:
                st.download_button("⬇️ CSV limpio",
                    df2_vista.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                    "telefonos_limpios.csv", "text/csv", use_container_width=True, type="primary")
            with d2:
                st.download_button("⬇️ CSV completo",
                    df2.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                    "telefonos_completo.csv", "text/csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PESTAÑA 4 — RFM Analytics
# ══════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📊 RFM Analytics — Inteligencia de Clientes")
    st.caption("Sube un historial de ventas y descubre quiénes son tus mejores clientes")

    uploaded4 = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"], key="up4")

    if uploaded4:
        df4 = pd.read_csv(uploaded4) if uploaded4.name.endswith('.csv') else pd.read_excel(uploaded4)
        st.success(f"✅ {len(df4):,} registros cargados")

        with st.expander("👁️ Vista previa", expanded=False):
            st.dataframe(df4.head(), use_container_width=True)

        st.markdown("#### 🗂️ Mapea tus columnas")

        KEYWORDS_ID     = ["id", "cliente", "rut", "customer", "cod"]
        KEYWORDS_FECHA  = ["fecha", "date", "compra", "venta", "order"]
        KEYWORDS_MONTO  = ["monto", "total", "valor", "amount", "precio", "venta"]

        col_id_det    = next((c for c in df4.columns if any(k in c.lower() for k in KEYWORDS_ID)), df4.columns[0])
        col_fecha_det = next((c for c in df4.columns if any(k in c.lower() for k in KEYWORDS_FECHA)), df4.columns[0])
        col_monto_det = next((c for c in df4.columns if any(k in c.lower() for k in KEYWORDS_MONTO)), df4.columns[0])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('**ID Cliente** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_id = st.selectbox("", df4.columns, index=list(df4.columns).index(col_id_det), key="rfm_id", label_visibility="collapsed")
        with c2:
            st.markdown('**Fecha Compra** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_fecha = st.selectbox("", df4.columns, index=list(df4.columns).index(col_fecha_det), key="rfm_fecha", label_visibility="collapsed")
        with c3:
            st.markdown('**Monto** <span class="tag tag-auto">✨ auto</span>', unsafe_allow_html=True)
            col_monto = st.selectbox("", df4.columns, index=list(df4.columns).index(col_monto_det), key="rfm_monto", label_visibility="collapsed")

        if st.button("📊 Calcular RFM", key="btn4"):
            with st.spinner("Calculando segmentos..."):
                df4[col_fecha] = pd.to_datetime(df4[col_fecha], dayfirst=True, errors='coerce')
                fecha_max = df4[col_fecha].max()

                rfm = df4.groupby(col_id).agg(
                    Recencia   = (col_fecha, lambda x: (fecha_max - x.max()).days),
                    Frecuencia = (col_id, 'count'),
                    Monto      = (col_monto, 'sum')
                ).reset_index()

                # Scoring por percentiles
                def score_percentil(serie, inverso=False):
                    pct = serie.rank(pct=True)
                    if inverso:
                        pct = 1 - pct
                    return pd.cut(pct, bins=4, labels=[1,2,3,4]).astype(int)

                rfm['R'] = score_percentil(rfm['Recencia'],   inverso=True)
                rfm['F'] = score_percentil(rfm['Frecuencia'], inverso=False)
                rfm['M'] = score_percentil(rfm['Monto'],      inverso=False)
                rfm['RFM_Score'] = rfm['R'] + rfm['F'] + rfm['M']

                def segmentar(score):
                    if score >= 11: return '🏆 Campeón'
                    elif score >= 9: return '💛 Leal'
                    elif score >= 7: return '🌱 Potencial'
                    elif score >= 5: return '⚠️ En Riesgo'
                    else: return '❌ Perdido'

                rfm['Segmento'] = rfm['RFM_Score'].apply(segmentar)

            # Métricas
            st.divider()
            segmentos = rfm['Segmento'].value_counts()
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("🏆 Campeones",   segmentos.get('🏆 Campeón', 0))
            m2.metric("💛 Leales",      segmentos.get('💛 Leal', 0))
            m3.metric("🌱 Potenciales", segmentos.get('🌱 Potencial', 0))
            m4.metric("⚠️ En Riesgo",  segmentos.get('⚠️ En Riesgo', 0))
            m5.metric("❌ Perdidos",    segmentos.get('❌ Perdido', 0))

            # Gráficos
            st.divider()
            g1, g2 = st.columns(2)

            with g1:
                fig_pie = px.pie(
                    rfm, names='Segmento',
                    title='Distribución de Segmentos',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with g2:
                fig_bar = px.bar(
                    rfm.groupby('Segmento')['Monto'].sum().reset_index(),
                    x='Segmento', y='Monto',
                    title='Ingresos por Segmento',
                    color='Segmento',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # Scatter RFM
            fig_scatter = px.scatter(
                rfm, x='Recencia', y='Frecuencia', size='Monto',
                color='Segmento', hover_data=[col_id],
                title='Mapa RFM — Recencia vs Frecuencia (tamaño = Monto)',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            st.dataframe(rfm, use_container_width=True)

            d1, d2 = st.columns(2)
            with d1:
                en_riesgo = rfm[rfm['Segmento'] == '⚠️ En Riesgo']
                st.download_button("⬇️ Descargar clientes En Riesgo",
                    en_riesgo.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                    "clientes_en_riesgo.csv", "text/csv",
                    use_container_width=True, type="primary")
            with d2:
                st.download_button("⬇️ Descargar RFM completo",
                    rfm.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                    "rfm_completo.csv", "text/csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PESTAÑA 5 — Diagnóstico Gratuito
# ══════════════════════════════════════════════════════════════
with tab5:
    st.subheader("🩺 Diagnóstico Gratuito de tu Base de Datos")
    st.caption("Sube tu archivo y recibe un reporte de salud en segundos — sin costo")

    uploaded5 = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"], key="up5")

    if uploaded5:
        df5 = pd.read_csv(uploaded5) if uploaded5.name.endswith('.csv') else pd.read_excel(uploaded5)
        st.success(f"✅ {len(df5):,} registros cargados — {len(df5.columns)} columnas")

        if st.button("🩺 Generar Diagnóstico", key="btn5"):
            with st.spinner("Analizando tu base de datos..."):
                reporte = {}

                # Analizar cada columna
                for col in df5.columns:
                    col_lower = col.lower()
                    muestra = df5[col].dropna().astype(str)

                    # RUT
                    if any(k in col_lower for k in ['rut', 'run']):
                        validos = muestra.apply(lambda x: validar_rut(x)['valido']).sum()
                        reporte['rut'] = {'col': col, 'validos': int(validos), 'total': len(muestra),
                                          'pct': round(validos/len(muestra)*100 if len(muestra) else 0, 1)}

                    # Email
                    elif any(k in col_lower for k in ['email', 'mail', 'correo']):
                        def check_email(e):
                            try: validate_email(e, check_deliverability=False); return True
                            except: return False
                        validos = muestra.apply(check_email).sum()
                        reporte['email'] = {'col': col, 'validos': int(validos), 'total': len(muestra),
                                            'pct': round(validos/len(muestra)*100 if len(muestra) else 0, 1)}

                    # Teléfono
                    elif any(k in col_lower for k in ['telefono', 'fono', 'phone', 'celular', 'movil']):
                        def check_tel(t):
                            try:
                                import re
                                limpio = re.sub(r'[^\d]', '', str(t))
                                if len(limpio) == 9 and limpio.startswith('9'): limpio = '+56' + limpio
                                elif len(limpio) == 11 and limpio.startswith('56'): limpio = '+' + limpio
                                p = phonenumbers.parse(limpio, 'CL')
                                return phonenumbers.is_possible_number(p)
                            except: return False
                        validos = muestra.apply(check_tel).sum()
                        reporte['telefono'] = {'col': col, 'validos': int(validos), 'total': len(muestra),
                                               'pct': round(validos/len(muestra)*100 if len(muestra) else 0, 1)}

                    # Comuna
                    elif any(k in col_lower for k in ['comuna', 'ciudad', 'localidad']):
                        validos = muestra.apply(lambda x: validar_comuna(x)['valida']).sum()
                        reporte['comuna'] = {'col': col, 'validos': int(validos), 'total': len(muestra),
                                             'pct': round(validos/len(muestra)*100 if len(muestra) else 0, 1)}

                # Duplicados
                dupes = df5.duplicated().sum()
                reporte['duplicados'] = {'total': int(dupes), 'pct': round(dupes/len(df5)*100, 1)}

                # Valores nulos
                nulos = df5.isnull().sum().sum()
                reporte['nulos'] = {'total': int(nulos), 'pct': round(nulos/(len(df5)*len(df5.columns))*100, 1)}

            # Score general
            scores = []
            if 'rut'      in reporte: scores.append(reporte['rut']['pct'])
            if 'email'    in reporte: scores.append(reporte['email']['pct'])
            if 'telefono' in reporte: scores.append(reporte['telefono']['pct'])
            if 'comuna'   in reporte: scores.append(reporte['comuna']['pct'])
            score_general = round(sum(scores)/len(scores) if scores else 0)

            # Semáforo
            if score_general >= 80:
                color, emoji, estado = '#a6e3a1', '🟢', 'Buena'
            elif score_general >= 50:
                color, emoji, estado = '#f9e2af', '🟡', 'Regular'
            else:
                color, emoji, estado = '#f38ba8', '🔴', 'Crítica'

            st.divider()
            st.markdown(f"""
            <div style='background:#1e1e2e; border-radius:16px; padding:2rem; text-align:center; border: 2px solid {color}'>
                <div style='font-size:4rem'>{emoji}</div>
                <div style='font-size:3rem; font-weight:800; color:{color}'>{score_general}/100</div>
                <div style='font-size:1.2rem; color:#cdd6f4'>Salud de Datos: <strong>{estado}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            st.subheader("📋 Detalle por campo")

            campos = {
                'rut':      ('🪪 RUT',       '#667eea'),
                'email':    ('📧 Email',      '#a6e3a1'),
                'telefono': ('📱 Teléfono',   '#f9e2af'),
                'comuna':   ('🏙️ Comuna',     '#89b4fa'),
            }

            cols = st.columns(len([k for k in campos if k in reporte]) or 1)
            i = 0
            for key, (label, color) in campos.items():
                if key in reporte:
                    r = reporte[key]
                    invalidos = r['total'] - r['validos']
                    with cols[i]:
                        st.markdown(f"""
                        <div style='background:#1e1e2e; border-radius:12px; padding:1.2rem; border:1px solid #313244'>
                            <div style='font-size:1rem; color:#a6adc8'>{label}</div>
                            <div style='font-size:2rem; font-weight:700; color:{color}'>{r['pct']}%</div>
                            <div style='font-size:0.8rem; color:#6c7086'>válidos</div>
                            <hr style='border-color:#313244'>
                            <div style='font-size:0.85rem'>✅ {r['validos']:,} válidos</div>
                            <div style='font-size:0.85rem'>❌ {invalidos:,} con problemas</div>
                        </div>
                        """, unsafe_allow_html=True)
                    i += 1

            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                st.metric("🔍 Filas duplicadas", f"{reporte['duplicados']['total']:,}",
                          f"{reporte['duplicados']['pct']}% del total")
            with g2:
                st.metric("⬜ Valores vacíos", f"{reporte['nulos']['total']:,}",
                          f"{reporte['nulos']['pct']}% del total")

            st.divider()
            st.info("💡 ¿Quieres corregir estos problemas? Usa las herramientas en las pestañas anteriores.")