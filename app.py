import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(
    page_title="Control de Producción y Orómetros",
    page_icon="🚜",
    layout="centered"
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE APPS SCRIPT (WEBHOOK)
# ---------------------------------------------------------
# Reemplaza esta URL con la URL de tu WebApp desplegada en Google Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbz36kbfHXjUt3eJ4eZ6QWKwbJ2UkfD64SGdUqD4BjUDcJmdKN7xis0m64KekSv-kEmd/exec"

# ---------------------------------------------------------
# INICIALIZACIÓN DEL ESTADO DE SESIÓN (PERSISTENCIA)
# ---------------------------------------------------------
if "jornada_activa" not in st.session_state:
    st.session_state.jornada_activa = False

if "orometro_inicio_m1" not in st.session_state:
    st.session_state.orometro_inicio_m1 = 0.0

if "orometro_inicio_m2" not in st.session_state:
    st.session_state.orometro_inicio_m2 = 0.0

if "registros_pesos" not in st.session_state:
    st.session_state.registros_pesos = []

if "fecha_inicio_jornada" not in st.session_state:
    st.session_state.fecha_inicio_jornada = None

# ---------------------------------------------------------
# ENCABEZADO Y BARRA LATERAL
# ---------------------------------------------------------
st.title("🚜 Registro de Jornada de Producción")

with st.sidebar:
    st.header("📌 Estado de la Jornada")
    if st.session_state.jornada_activa:
        st.success("🟢 JORNADA EN PROGRESO")
        st.info(f"**Inicio:** {st.session_state.fecha_inicio_jornada}")
        st.write(f"**Orómetro Inic. M1:** {st.session_state.orometro_inicio_m1} hrs")
        st.write(f"**Orómetro Inic. M2:** {st.session_state.orometro_inicio_m2} hrs")
        st.write(f"**Registros guardados:** {len(st.session_state.registros_pesos)}")
    else:
        st.warning("🔴 JORNADA NO INICIADA")

# ---------------------------------------------------------
# 1. PANTALLA DE INICIO DE JORNADA
# ---------------------------------------------------------
if not st.session_state.jornada_activa:
    st.subheader("🏁 Iniciar Nueva Jornada de Trabajo")
    st.write("Ingrese los orómetros iniciales de ambas máquinas para habilitar el registro de peso.")

    with st.form("form_inicio_jornada"):
        col1, col2 = st.columns(2)
        with col1:
            oro_m1 = st.number_input("Orómetro Inicial - Máquina 1 (hrs)", min_value=0.0, step=0.1, format="%.1f")
        with col2:
            oro_m2 = st.number_input("Orómetro Inicial - Máquina 2 (hrs)", min_value=0.0, step=0.1, format="%.1f")
        
        btn_iniciar = st.form_submit_button("🚀 Iniciar Jornada", use_container_width=True)

        if btn_iniciar:
            if oro_m1 >= 0 and oro_m2 >= 0:
                st.session_state.jornada_activa = True
                st.session_state.orometro_inicio_m1 = oro_m1
                st.session_state.orometro_inicio_m2 = oro_m2
                st.session_state.fecha_inicio_jornada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.registros_pesos = []
                st.success("¡Jornada iniciada con éxito! Ya puede registrar la producción.")
                st.rerun()
            else:
                st.error("Por favor ingrese valores de orómetro válidos.")

# ---------------------------------------------------------
# 2. PANTALLA DE REGISTRO DURANTE LA JORNADA
# ---------------------------------------------------------
else:
    st.subheader("⚖️ Registro de Pesos / Producción")

    with st.form("form_registro_peso", clear_on_submit=True):
        col_m, col_p = st.columns(2)
        with col_m:
            maquina = st.selectbox("Seleccionar Máquina", ["Máquina 1", "Máquina 2"])
        with col_p:
            peso_ton = st.number_input("Peso Registrado (Toneladas)", min_value=0.01, step=0.01, format="%.2f")
        
        observaciones = st.text_input("Observaciones o notas (opcional)")
        btn_guardar_peso = st.form_submit_button("➕ Guardar Registro", use_container_width=True)

        if btn_guardar_peso:
            nuevo_registro = {
                "hora": datetime.now().strftime("%H:%M:%S"),
                "maquina": maquina,
                "peso_ton": peso_ton,
                "observaciones": observaciones
            }
            st.session_state.registros_pesos.append(nuevo_registro)
            st.toast(f"✅ Registrado: {peso_ton} Ton en {maquina}", icon="✅")

    # Mostrar tabla de producción acumulada
    st.divider()
    st.write("### 📋 Producción Acumulada del Turno")
    
    if len(st.session_state.registros_pesos) > 0:
        df_registros = pd.DataFrame(st.session_state.registros_pesos)
        st.dataframe(df_registros, use_container_width=True)

        # Totales parciales
        ton_m1 = sum(r["peso_ton"] for r in st.session_state.registros_pesos if r["maquina"] == "Máquina 1")
        ton_m2 = sum(r["peso_ton"] for r in st.session_state.registros_pesos if r["maquina"] == "Máquina 2")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Máquina 1", f"{ton_m1:.2f} Ton")
        c2.metric("Total Máquina 2", f"{ton_m2:.2f} Ton")
        c3.metric("Total Jornada", f"{(ton_m1 + ton_m2):.2f} Ton")
    else:
        st.info("Aún no hay pesadas registradas en esta jornada.")

    # ---------------------------------------------------------
    # 3. FINALIZAR JORNADA Y ENVIAR A GOOGLE DRIVE / SHEETS
    # ---------------------------------------------------------
    st.divider()
    st.subheader("🏁 Cierre de Jornada de Trabajo")

    with st.expander("🔻 Desplegar formulario para Finalizar Jornada", expanded=False):
        with st.form("form_fin_jornada"):
            st.write("Ingrese los orómetros finales para realizar los cálculos y guardar la información en Google Drive.")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                oro_fin_m1 = st.number_input(
                    "Orómetro Final - Máquina 1 (hrs)", 
                    min_value=st.session_state.orometro_inicio_m1, 
                    value=st.session_state.orometro_inicio_m1,
                    step=0.1, 
                    format="%.1f"
                )
            with col_f2:
                oro_fin_m2 = st.number_input(
                    "Orómetro Final - Máquina 2 (hrs)", 
                    min_value=st.session_state.orometro_inicio_m2, 
                    value=st.session_state.orometro_inicio_m2,
                    step=0.1, 
                    format="%.1f"
                )

            btn_cerrar_jornada = st.form_submit_button("🔒 Finalizar y Guardar Jornada", use_container_width=True)

            if btn_cerrar_jornada:
                # Cálculos de horas operativas
                horas_m1 = round(oro_fin_m1 - st.session_state.orometro_inicio_m1, 2)
                horas_m2 = round(oro_fin_m2 - st.session_state.orometro_inicio_m2, 2)

                # Cálculos de producción
                ton_m1 = sum(r["peso_ton"] for r in st.session_state.registros_pesos if r["maquina"] == "Máquina 1")
                ton_m2 = sum(r["peso_ton"] for r in st.session_state.registros_pesos if r["maquina"] == "Máquina 2")
                ton_total = ton_m1 + ton_m2

                # Rendimiento Ton/Hora
                rend_m1 = round(ton_m1 / horas_m1, 2) if horas_m1 > 0 else 0.0
                rend_m2 = round(ton_m2 / horas_m2, 2) if horas_m2 > 0 else 0.0

                payload = {
                    "fecha_inicio": st.session_state.fecha_inicio_jornada,
                    "fecha_fin": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "orometro_inicio_m1": st.session_state.orometro_inicio_m1,
                    "orometro_fin_m1": oro_fin_m1,
                    "horas_trabajadas_m1": horas_m1,
                    "toneladas_m1": ton_m1,
                    "rendimiento_ton_hr_m1": rend_m1,
                    "orometro_inicio_m2": st.session_state.orometro_inicio_m2,
                    "orometro_fin_m2": oro_fin_m2,
                    "horas_trabajadas_m2": horas_m2,
                    "toneladas_m2": ton_m2,
                    "rendimiento_ton_hr_m2": rend_m2,
                    "toneladas_totales": ton_total,
                    "detalle_registros": st.session_state.registros_pesos
                }

                # Envío de datos a Google Sheets mediante Webhook
                try:
                    response = requests.post(
                        WEBHOOK_URL, 
                        data=json.dumps(payload),
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ ¡Jornada registrada correctamente en Google Drive!")
                        st.balloons()

                        # Restablecer la aplicación desde cero para el siguiente turno
                        st.session_state.jornada_activa = False
                        st.session_state.orometro_inicio_m1 = 0.0
                        st.session_state.orometro_inicio_m2 = 0.0
                        st.session_state.registros_pesos = []
                        st.session_state.fecha_inicio_jornada = None

                        st.button("🔄 Iniciar Nuevo Turno", on_click=lambda: st.rerun())
                    else:
                        st.error(f"Error al guardar datos. Código de respuesta: {response.status_code}")
                except Exception as e:
                    st.error(f"Error de conexión con Google Drive/Sheets: {e}")
