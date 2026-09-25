import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Producción Biomasa", page_icon="🌱", layout="wide")

st.title("🌱 Registro de Producción de Biomasa")
st.markdown("Sistema de captura y visualización de datos de producción.")

ARCHIVO_DATOS = "produccion_biomasa.csv"

# Función para cargar datos existentes o crear el archivo
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        return pd.read_csv(ARCHIVO_DATOS)
    else:
        return pd.DataFrame(columns=["Fecha", "Lote", "Tipo Biomasa", "Peso (Kg)", "Humedad (%)", "Observaciones"])

df_datos = cargar_datos()

# Formulario de registro en la barra lateral
st.sidebar.header("📋 Nuevo Registro")

with st.sidebar.form(key="form_biomasa", clear_on_submit=True):
    fecha = st.date_input("Fecha de Registro", datetime.now())
    lote = st.text_input("Código de Lote / Ubicación", placeholder="Ej. Lote A-12")
    tipo = st.selectbox("Tipo de Biomasa", ["Aserrín / Madera", "Paja / Rastrojo", "Cáscara de Arroz", "Bagazo de Caña", "Otro"])
    peso = st.number_input("Peso Total (Kg)", min_value=0.0, step=10.0, format="%.2f")
    humedad = st.slider("Porcentaje de Humedad (%)", 0.0, 100.0, 15.0)
    observaciones = st.text_area("Observaciones", placeholder="Detalles sobre la recolección...")
    
    submit_button = st.form_submit_button(label="Guardar Registro")

# Procesar el envío del formulario
if submit_button:
    if not lote:
        st.sidebar.error("⚠️ El código de lote es obligatorio.")
    else:
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Lote": lote,
            "Tipo Biomasa": tipo,
            "Peso (Kg)": peso,
            "Humedad (%)": humedad,
            "Observaciones": observaciones
        }])
        
        df_datos = pd.concat([df_datos, nuevo_registro], ignore_index=True)
        df_datos.to_csv(ARCHIVO_DATOS, index=False)
        st.sidebar.success("✅ Registro guardado exitosamente.")

# Área de visualización principal
st.subheader("📊 Registros Acumulados")

if df_datos.empty:
    st.info("Aún no hay registros cargados. Utiliza el formulario lateral para añadir el primero.")
else:
    # Métricas clave
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Biomasa (Kg)", f"{df_datos['Peso (Kg)'].sum():,.2f}")
    col2.metric("Total de Registros", len(df_datos))
    col3.metric("Humedad Promedio", f"{df_datos['Humedad (%)'].mean():.1f}%")

    st.markdown("---")

    # Tabla interactiva
    st.dataframe(df_datos, use_container_width=True)

    # Opción de descarga
    csv_bytes = df_datos.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos en CSV",
        data=csv_bytes,
        file_name=f"produccion_biomasa_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )