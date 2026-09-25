import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(page_title="Producción Biomasa", page_icon="🪵", layout="wide")

st.title("🪵 Control de Producción de Biomasa")
st.markdown("Registro operativo para líneas de **Triturado** y **Chipper**")

ARCHIVO_DATOS = "produccion_biomasa.csv"

# Definición de productos por tipo de máquina
PRODUCTOS_PROCESO = {
    "Máquina Trituradora": [
        "Pallets reciclados",
        "Canasta de tablas",
        "Pallets de plywood"
    ],
    "Máquina Chipper": [
        "Jampa del proceso de aserrado",
        "Canastas de proceso de maquinado"
    ]
}

# Cargar o crear la estructura de datos
def cargar_datos():
    columnas = [
        "Fecha", "Turno", "Equipo de Trabajo", "Proceso / Máquina", "Producto",
        "Cantidad (Unidades)", "Peso Bruto (Kg)", "Tara Uñas (Kg)", "Peso Neto (Kg)",
        "Horómetro Inicio", "Horómetro Fin", "Horas Máquina", "Observaciones"
    ]
    if os.path.exists(ARCHIVO_DATOS):
        df = pd.read_csv(ARCHIVO_DATOS)
        # Asegurar compatibilidad si se agregan nuevas columnas
        for col in columnas:
            if col not in df.columns:
                df[col] = None
        return df[columnas]
    else:
        return pd.DataFrame(columns=columnas)

df_datos = cargar_datos()

# FORMULARIO DE REGISTRO EN BARRA LATERAL
st.sidebar.header("📋 Registrar Nuevo Lote")

with st.sidebar.form(key="form_registro_biomasa", clear_on_submit=False):
    st.subheader("1. Datos Turno y Operación")
    fecha = st.date_input("Fecha", datetime.now())
    turno = st.selectbox("Turno de Trabajo", ["Turno 1 (Día)", "Turno 2 (Noche)", "Turno 3 (Rotativo)"])
    equipo = st.text_input("Equipo de Trabajo / Operador", placeholder="Ej. Equipo A - Juan Pérez")
    
    st.subheader("2. Selección de Proceso y Producto")
    proceso = st.selectbox("Proceso / Máquina", list(PRODUCTOS_PROCESO.keys()))
    
    # Filtrar productos dinámicamente según el proceso seleccionado
    productos_disponibles = PRODUCTOS_PROCESO[proceso]
    producto = st.selectbox("Producto Ingresado", productos_disponibles)
    
    st.subheader("3. Pesaje (Montacargas)")
    cantidad = st.number_input("Cantidad de Unidades (Pallets/Canastas)", min_value=1, step=1, value=1)
    peso_bruto = st.number_input("Peso Bruto Balanza (Kg)", min_value=0.0, step=5.0, value=0.0)
    tara_unas = st.number_input("Tara de las Uñas (Kg)", min_value=0.0, step=1.0, value=50.0)
    
    st.subheader("4. Horómetro de la Máquina")
    horometro_inicio = st.number_input("Horómetro Inicio", min_value=0.0, step=0.1, value=0.0)
    horometro_fin = st.number_input("Horómetro Fin", min_value=0.0, step=0.1, value=0.0)
    
    observaciones = st.text_area("Observaciones", placeholder="Ej. Material con exceso de humedad, demoras...")
    
    submit_button = st.form_submit_button(label="📌 Registrar Carga")

# PROCESAMIENTO DEL REGISTRO
if submit_button:
    # Validaciones básicas
    if peso_bruto <= tara_unas and peso_bruto > 0:
        st.sidebar.error("⚠️ El Peso Bruto debe ser mayor a la Tara de las uñas.")
    elif horometro_fin < horometro_inicio:
        st.sidebar.error("⚠️ El Horómetro Fin no puede ser menor al Horómetro Inicio.")
    elif not equipo:
        st.sidebar.error("⚠️ Debe ingresar el nombre del Equipo de Trabajo.")
    else:
        peso_neto = max(0.0, peso_bruto - tara_unas)
        horas_trabajadas = round(horometro_fin - horometro_inicio, 2)
        
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Turno": turno,
            "Equipo de Trabajo": equipo,
            "Proceso / Máquina": proceso,
            "Producto": producto,
            "Cantidad (Unidades)": cantidad,
            "Peso Bruto (Kg)": peso_bruto,
            "Tara Uñas (Kg)": tara_unas,
            "Peso Neto (Kg)": peso_neto,
            "Horómetro Inicio": horometro_inicio,
            "Horómetro Fin": horometro_fin,
            "Horas Máquina": horas_trabajadas,
            "Observaciones": observaciones
        }])
        
        df_datos = pd.concat([df_datos, nuevo_registro], ignore_index=True)
        df_datos.to_csv(ARCHIVO_DATOS, index=False)
        st.sidebar.success("✅ ¡Registro agregado exitosamente!")
        st.rerun()

# PANEL DE VISUALIZACIÓN Y REPORTES
st.subheader("📊 Resumen Acumulado de Producción")

if df_datos.empty:
    st.info("No hay registros almacenados. Ingresa la primera carga usando el formulario de la izquierda.")
else:
    # Indicadores globales (KPIs)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Producción Total (Kg Neto)", f"{df_datos['Peso Neto (Kg)'].sum():,.2f}")
    kpi2.metric("Total Unidades Procesadas", f"{int(df_datos['Cantidad (Unidades)'].sum()):,}")
    kpi3.metric("Total Horas Máquina", f"{df_datos['Horas Máquina'].sum():,.2f} hrs")
    kpi4.metric("Registros de Cargas", len(df_datos))

    st.markdown("---")

    # Resumen agrupado por Proceso y Producto
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 🛠️ Producción por Máquina")
        resumen_maquina = df_datos.groupby("Proceso / Máquina")[["Cantidad (Unidades)", "Peso Neto (Kg)", "Horas Máquina"]].sum()
        st.dataframe(resumen_maquina, use_container_width=True)

    with col_right:
        st.markdown("### 📦 Producción por Tipo de Producto")
        resumen_producto = df_datos.groupby(["Proceso / Máquina", "Producto"])[["Cantidad (Unidades)", "Peso Neto (Kg)"]].sum()
        st.dataframe(resumen_producto, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📑 Detalle General de Transacciones")
    st.dataframe(df_datos, use_container_width=True)

    # Exportar a Excel / CSV
    st.markdown("### 📥 Exportar Datos")
    col_exp1, col_exp2 = st.columns(2)
    
    csv_bytes = df_datos.to_csv(index=False).encode('utf-8')
    col_exp1.download_button(
        label="📄 Descargar reporte en CSV",
        data=csv_bytes,
        file_name=f"reporte_biomasa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
