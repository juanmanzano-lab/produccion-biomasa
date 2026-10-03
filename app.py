import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import zoneinfo

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Pesajes y Producción",
    page_icon="⚖️",
    layout="centered"
)

# Zona horaria de Ecuador (Quito / Guayaquil - GMT-5)
ZONA_HORARIA_ECUADOR = zoneinfo.ZoneInfo("America/Guayaquil")

# ---------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE APPS SCRIPT (WEBHOOK)
# ---------------------------------------------------------
# Reemplaza esta URL con la URL de tu WebApp desplegada en Google Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzInH-c1vHdHGFJ_DAx5yF9frqlHtAh2an7wx8hNFNCn5cEYF2lVnLIkQ-EytkCRUfC/exec"

# ---------------------------------------------------------
# INICIALIZACIÓN DE MEMORIA DE SESIÓN (PERSISTENCIA SIN ALTERAR INTERFAZ)
# ---------------------------------------------------------
if "registros" not in st.session_state:
    st.session_state.registros = []

if "orometro_chipper_inicio" not in st.session_state:
    st.session_state.orometro_chipper_inicio = 0.0

if "orometro_trituradora_inicio" not in st.session_state:
    st.session_state.orometro_trituradora_inicio = 0.0

if "hora_inicio_jornada" not in st.session_state:
    st.session_state.hora_inicio_jornada = None

# ---------------------------------------------------------
# INTERFAZ PRINCIPAL (ESTRUKTURA ORIGINAL DE REGISTRO)
# ---------------------------------------------------------
st.title("📋 Control de Producción y Orómetros")

# Registro de Orómetros de Inicio de Jornada
st.subheader("⚙️ Orómetros al Inicio de Jornada")
col_o1, col_o2 = st.columns(2)

with col_o1:
    oro_chip_inic = st.number_input(
        "Orómetro Inicial Chipper (hrs)",
        min_value=0.0,
        value=float(st.session_state.orometro_chipper_inicio),
        step=0.1,
        format="%.1f",
        key="input_oro_chip_inic"
    )
    st.session_state.orometro_chipper_inicio = oro_chip_inic

with col_o2:
    oro_trit_inic = st.number_input(
        "Orómetro Inicial Trituradora (hrs)",
        min_value=0.0,
        value=float(st.session_state.orometro_trituradora_inicio),
        step=0.1,
        format="%.1f",
        key="input_oro_trit_inic"
    )
    st.session_state.orometro_trituradora_inicio = oro_trit_inic

st.divider()

# ---------------------------------------------------------
# FORMULARIO DE REGISTRO DE PESO
# ---------------------------------------------------------
st.subheader("⚖️ Ingreso de Pesadas")

with st.form("form_peso", clear_on_submit=True):
    col_m, col_p = st.columns(2)
    
    with col_m:
        maquina = st.selectbox("Seleccionar Máquina", ["Chipper", "Trituradora"])
        
    with col_p:
        peso = st.number_input("Peso Registrado (Toneladas / Kg)", min_value=0.0, step=0.01, format="%.2f")
        
    observacion = st.text_input("Observaciones (opcional)")
    
    btn_guardar = st.form_submit_button("➕ Registrar Peso", use_container_width=True)
    
    if btn_guardar:
        if peso > 0:
            # Obtener fecha y hora exacta en zona horaria de Ecuador
            ahora_ecuador = datetime.now(ZONA_HORARIA_ECUADOR)
            
            if st.session_state.hora_inicio_jornada is None:
                st.session_state.hora_inicio_jornada = ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S")

            nuevo_registro = {
                "fecha_hora": ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S"),
                "hora_corta": ahora_ecuador.strftime("%H:%M:%S"),
                "maquina": maquina,
                "peso": peso,
                "observacion": observacion
            }
            
            # Guardar en el estado de sesión persistente
            st.session_state.registros.append(nuevo_registro)
            st.success(f"✅ Registrado en {maquina}: {peso} a las {nuevo_registro['hora_corta']} (Hora Ecuador)")
        else:
            st.warning("Ingrese un peso mayor a 0.")

# ---------------------------------------------------------
# TABLA DE REGISTROS ACUMULADOS EN LA JORNADA
# ---------------------------------------------------------
st.divider()
st.subheader("📊 Registros de la Jornada Actual")

if len(st.session_state.registros) > 0:
    df = pd.DataFrame(st.session_state.registros)
    st.dataframe(df[["hora_corta", "maquina", "peso", "observacion"]], use_container_width=True)
    
    # Cálculos acumulados
    total_chipper = sum(r["peso"] for r in st.session_state.registros if r["maquina"] == "Chipper")
    total_trituradora = sum(r["peso"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Chipper", f"{total_chipper:.2f}")
    c2.metric("Total Trituradora", f"{total_trituradora:.2f}")
    c3.metric("Total Jornada", f"{(total_chipper + total_trituradora):.2f}")
else:
    st.info("No hay pesadas registradas en esta jornada.")

# ---------------------------------------------------------
# CIERRE Y FINALIZACIÓN DE JORNADA
# ---------------------------------------------------------
st.divider()
st.subheader("🏁 Finalizar Jornada de Trabajo")

with st.expander("🔻 Presiona aquí para ingresar orómetros finales y cerrar jornada"):
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        oro_chip_fin = st.number_input(
            "Orómetro Final Chipper (hrs)",
            min_value=st.session_state.orometro_chipper_inicio,
            value=st.session_state.orometro_chipper_inicio,
            step=0.1,
            format="%.1f"
        )
        
    with col_f2:
        oro_trit_fin = st.number_input(
            "Orómetro Final Trituradora (hrs)",
            min_value=st.session_state.orometro_trituradora_inicio,
            value=st.session_state.orometro_trituradora_inicio,
            step=0.1,
            format="%.1f"
        )
        
    btn_finalizar = st.button("🔴 CERRAR Y GUARDAR JORNADA", use_container_width=True, type="primary")
    
    if btn_finalizar:
        if len(st.session_state.registros) == 0:
            st.error("No se puede cerrar la jornada sin haber registrado pesadas.")
        else:
            ahora_fin = datetime.now(ZONA_HORARIA_ECUADOR)
            
            # Cálculos de rendimiento
            hrs_chipper = round(oro_chip_fin - st.session_state.orometro_chipper_inicio, 2)
            hrs_trituradora = round(oro_trit_fin - st.session_state.orometro_trituradora_inicio, 2)
            
            total_chipper = sum(r["peso"] for r in st.session_state.registros if r["maquina"] == "Chipper")
            total_trituradora = sum(r["peso"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
            
            rend_chipper = round(total_chipper / hrs_chipper, 2) if hrs_chipper > 0 else 0.0
            rend_trituradora = round(total_trituradora / hrs_trituradora, 2) if hrs_trituradora > 0 else 0.0
            
            # Objeto de envío
            payload = {
                "fecha_inicio": st.session_state.hora_inicio_jornada,
                "fecha_fin": ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
                "orometro_inicio_chipper": st.session_state.orometro_chipper_inicio,
                "orometro_fin_chipper": oro_chip_fin,
                "horas_chipper": hrs_chipper,
                "total_peso_chipper": total_chipper,
                "rendimiento_chipper": rend_chipper,
                "orometro_inicio_trituradora": st.session_state.orometro_trituradora_inicio,
                "orometro_fin_trituradora": oro_trit_fin,
                "horas_trituradora": hrs_trituradora,
                "total_peso_trituradora": total_trituradora,
                "rendimiento_trituradora": rend_trituradora,
                "peso_total_jornada": total_chipper + total_trituradora,
                "detalle_pesadas": st.session_state.registros
            }
            
            # Enviar datos al Webhook de Google Apps Script
            try:
                res = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
                if res.status_code == 200:
                    st.success("🎉 ¡Jornada finalizada y guardada exitosamente en Google Drive!")
                    
                    # Limpieza completa de la sesión para la nueva jornada
                    st.session_state.registros = []
                    st.session_state.orometro_chipper_inicio = 0.0
                    st.session_state.orometro_trituradora_inicio = 0.0
                    st.session_state.hora_inicio_jornada = None
                    
                    st.button("🔄 Comenzar Nueva Jornada", on_click=lambda: st.rerun())
                else:
                    st.error(f"Error al enviar datos. Código servidor: {res.status_code}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
