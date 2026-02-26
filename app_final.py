import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. LÓGICA DE RUTAS INTELIGENTE (PORTABILIDAD) ---
if os.path.exists('/content/drive/MyDrive'):
    # Si detecta Google Colab
    RUTA_BASE = '/content/drive/MyDrive/UNAM/Servicio Social/IER/Desarrollo del proyecto/PYTHON/proyecto_python'
else:
    # Si está en un servidor local o remoto (GitHub / VPS)
    RUTA_BASE = os.path.dirname(os.path.abspath(__file__))

RUTA_OUTPUTS = os.path.join(RUTA_BASE, 'outputs')
RUTA_ENIGH = os.path.join(RUTA_BASE, 'ENIGH')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard ENIGH - IER", layout="wide")
st.title("📊 Análisis Multivariado del Consumo Energético")
st.markdown("Servicio Social - IER UNAM | **Prototipo de Visualización v1.1**")

# --- 3. DICCIONARIO OFICIAL INEGI ---
dicc_entidades = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur", 4: "Campeche",
    5: "Coahuila de Zaragoza", 6: "Colima", 7: "Chiapas", 8: "Chihuahua",
    9: "Ciudad de México", 10: "Durango", 11: "Guanajuato", 12: "Guerrero",
    13: "Hidalgo", 14: "Jalisco", 15: "México", 16: "Michoacán de Ocampo",
    17: "Morelos", 18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca",
    21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas",
    29: "Tlaxcala", 30: "Veracruz de Ignacio de la Llave", 31: "Yucatán", 32: "Zacatecas"
}

# --- 4. FUNCIONES DE CARGA ---
@st.cache_data
def cargar_base(ruta_archivo, filas=None, columnas=None):
    if os.path.exists(ruta_archivo):
        try:
            return pd.read_csv(ruta_archivo, low_memory=False, nrows=filas, usecols=columnas)
        except:
            return None
    return None

# Carga de archivos de la carpeta outputs
prep = cargar_base(os.path.join(RUTA_OUTPUTS, "01_preparacion_pca.csv"))
varianza = cargar_base(os.path.join(RUTA_OUTPUTS, "02_varianza_explicada_pca.csv"))
nodos = cargar_base(os.path.join(RUTA_OUTPUTS, "03_red_nodos.csv"))
aristas = cargar_base(os.path.join(RUTA_OUTPUTS, "03_red_aristas.csv"))
centralidad = cargar_base(os.path.join(RUTA_OUTPUTS, "04_centralidad.csv"))

# --- 5. PROCESAMIENTO DE ETIQUETAS ---
if prep is not None:
    if 'sexo_jefe' in prep.columns:
        prep['sexo_label'] = prep['sexo_jefe'].apply(lambda x: 'Hombre' if x == 1 else 'Mujer')
    if 'entidad' in prep.columns:
        val_u = sorted(prep['entidad'].unique())
        map_ent = {val: dicc_entidades.get(val, f"Edo {val}") for val in val_u}
        prep['entidad_label'] = prep['entidad'].map(map_ent)

# --- 6. PESTAÑAS DEL DASHBOARD ---
tabs = st.tabs(["📊 Exploración ENIGH", "📂 Datos Preparados", "📈 PCA", "🕸 Redes", "⭐ Centralidad", "📁 Dataset Maestro"])

# --- TAB 0: EXPLORACIÓN DINÁMICA ---
with tabs[0]:
    st.subheader("Buscador Dinámico de Microdatos")
    if os.path.exists(RUTA_ENIGH):
        anios = sorted([d for d in os.listdir(RUTA_ENIGH) if os.path.isdir(os.path.join(RUTA_ENIGH, d))])
        if anios:
            c1, c2 = st.columns(2)
            anio_sel = c1.selectbox("1. Año", anios, key="sb_anio")
            path_anio = os.path.join(RUTA_ENIGH, anio_sel)
            bases = [f for f in os.listdir(path_anio) if f.endswith(".csv")]
            if bases:
                base_sel = c2.selectbox("2. Tabla", bases, key="sb_base")
                df_h = pd.read_csv(os.path.join(path_anio, base_sel), nrows=0)
                seleccionadas = st.multiselect("3. Columnas:", df_h.columns.tolist(), default=df_h.columns.tolist()[:5])
                if seleccionadas:
                    df_exp = pd.read_csv(os.path.join(path_anio, base_sel), usecols=seleccionadas, nrows=100)
                    st.dataframe(df_exp.head(15))
                    st.download_button("⬇️ Descargar selección", df_exp.to_csv(index=False), "exploracion.csv")
    else:
        st.info("No se encontró la carpeta ENIGH. Verifique la ruta.")

# --- TAB 1: DATOS PREPARADOS ---
with tabs[1]:
    st.subheader("Vista Previa de Datos Normalizados")
    if prep is not None:
        st.dataframe(prep.head(50))
        st.download_button("⬇️ Descargar CSV", prep.to_csv(index=False), "datos_procesados.csv")

# --- TAB 2: PCA Y MÉTRICAS ---
with tabs[2]:
    st.subheader("📈 Análisis de Componentes Principales")
    if varianza is not None:
        cv1, cv2 = st.columns(2)
        cv1.plotly_chart(px.bar(varianza, x="Componente", y="Varianza_explicada", title="Varianza por Componente"), use_container_width=True)
        cv2.plotly_chart(px.line(varianza, x="Componente", y="Varianza_acumulada", markers=True, title="Varianza Acumulada"), use_container_width=True)
    
    if prep is not None:
        st.markdown("---")
        f1, f2 = st.columns(2)
        s_sel = f1.selectbox("Sexo Jefe/a", ["Todos", "Hombre", "Mujer"], key="pca_sexo")
        e_sel = f2.selectbox("Estado", ["Todas"] + list(prep['entidad_label'].unique()), key="pca_entidad")
        
        df_f = prep.copy()
        if s_sel != "Todos": df_f = df_f[df_f['sexo_label'] == s_sel]
        if e_sel != "Todas": df_f = df_f[df_f['entidad_label'] == e_sel]
        
        if 'PC1' in df_f.columns:
            st.plotly_chart(px.scatter(df_f, x="PC1", y="PC2", color="sexo_label", title="Dispersión de Hogares"), use_container_width=True)

        st.markdown("#### ⚡ Resumen de la Selección")
        m1, m2, m3 = st.columns(3)
        m1.metric("Hogares", f"{len(df_f):,}")
        # Estas columnas aparecerán con valores reales solo si ejecutas el script de integración previo
        ing = df_f['ingreso_real'].mean() if 'ingreso_real' in df_f.columns else 0
        gas = df_f['gasto_real'].mean() if 'gasto_real' in df_f.columns else 0
        m2.metric("Ingreso Promedio", f"${ing:,.2f}")
        m3.metric("Gasto Energía Prom.", f"${gas:,.2f}")

# --- TAB 3: REDES ---
with tabs[3]:
    st.subheader("🕸️ Redes de Variables Energéticas")
    if nodos is not None and aristas is not None:
        cn, ca = st.columns(2)
        with cn:
            st.write("**Nodos**")
            st.dataframe(nodos)
        with ca:
            st.write("**Aristas (Conexiones)**")
            st.dataframe(aristas.head(100))
    else:
        st.warning("Archivos de Red no detectados en /outputs.")

# --- TAB 4: CENTRALIDAD ---
with tabs[4]:
    st.subheader("⭐ Importancia de Variables")
    if centralidad is not None:
        met = st.selectbox("Seleccione Métrica", [c for c in centralidad.columns if c != 'variable'])
        fig = px.bar(centralidad.sort_values(by=met, ascending=False).head(15), x="variable", y=met, color=met)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 5: DATASET MAESTRO ---
with tabs[5]:
    st.subheader("📁 Estructura Familiar (Maestro)")
    df_maestro = cargar_base(os.path.join(RUTA_OUTPUTS, "estructura_familiar_2024.csv"), filas=100)
    if df_maestro is not None:
        st.dataframe(df_maestro.head(20))
        st.download_button("⬇️ Descargar Maestro", df_maestro.to_csv(index=False), "maestro_completo.csv")

st.sidebar.markdown(f"**Estado del Servidor:** ✅ Online")
st.sidebar.markdown(f"**Ruta Activa:** `{RUTA_BASE}`")