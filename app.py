import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import zoneinfo

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ZONA HORARIA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Pesajes en Tiempo Real",
    page_icon="⚖️",
    layout="centered"
)

# Zona horaria oficial de Ecuador (GMT-5)
ZONA_HORARIA_ECUADOR = zoneinfo.ZoneInfo("America/Guayaquil")

# ---------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE APPS SCRIPT (WEBHOOK)
# ---------------------------------------------------------
# Pega aquí la URL resultante al desplegar Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/TU_SCRIPT_ID_AQUI/exec"

# CONSTANTE TARA MONTACARGAS
TARA_UÑAS_KG = 120.0

# OPCIONES DE PRODUCTOS SEGÚN LA MÁQUINA SELECCIONADA
PRODUCTOS_POR_MAQUINA = {
    "Chipper": [
        "Troncos / Trozas",
        "Ramas / Ramaje",
        "Costeros / Desechos de Madera",
        "Corteza",
        "Otro"
    ],
    "Trituradora": [
        "Pallets / Tarimas",
        "Residuos Plásticos",
        "Madera Procesada / Chatarra",
        "Restos Agrícolas",
        "Otro"
    ]
}

# ---------------------------------------------------------
# MEMORIA DE SESIÓN (ESTADO LOCAL)
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
# INTERFAZ PRINCIPAL
# ---------------------------------------------------------
st.title("📋 Registro de Pesajes y Producción (Tiempo Real)")

# 1. ORÓMETROS DE INICIO DE JORNADA
st.subheader("⚙️ 1. Orómetros Iniciales del Turno")
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

# 2. FORMULARIO DE REGISTRO DE PESO
st.subheader("⚖️ 2. Ingreso de Pesadas (Guardado directo a Drive)")

# Selección de máquina
maquina_sel = st.selectbox("Máquina", ["Chipper", "Trituradora"])

# Desplegable de productos dinámico según máquina
productos_disponibles = PRODUCTOS_POR_MAQUINA[maquina_sel]
producto_sel = st.selectbox("Producto", productos_disponibles)

col_u, col_p = st.columns(2)
with col_u:
    unidades = st.number_input("Cantidad / Unidades", min_value=1, step=1, value=1)
with col_p:
    peso_bruto_kg = st.number_input("Peso Registrado Bruto (kg)", min_value=0.0, step=0.5, format="%.2f")

# Cálculo automático de peso neto
peso_neto_kg = max(0.0, peso_bruto_kg - TARA_UÑAS_KG) if peso_bruto_kg > 0 else 0.0

st.info(f"💡 **Tara fija uñas montacargas:** {TARA_UÑAS_KG:.0f} kg | **Peso Neto a registrar:** {peso_neto_kg:.2f} kg")

observacion = st.text_input("Observaciones (opcional)")

btn_guardar_pesada = st.button("➕ REGISTRAR PESO (ENVIAR A DRIVE)", use_container_width=True, type="primary")

if btn_guardar_pesada:
    if peso_bruto_kg > 0:
        ahora_ecuador = datetime.now(ZONA_HORARIA_ECUADOR)
        
        if st.session_state.hora_inicio_jornada is None:
            st.session_state.hora_inicio_jornada = ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S")

        registro_payload = {
            "tipo_evento": "REGISTRO_PESO",
            "fecha_hora": ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S"),
            "hora_corta": ahora_ecuador.strftime("%H:%M:%S"),
            "maquina": maquina_sel,
            "producto": producto_sel,
            "unidades": int(unidades),
            "peso_bruto_kg": float(peso_bruto_kg),
            "tara_kg": float(TARA_UÑAS_KG),
            "peso_neto_kg": float(peso_neto_kg),
            "observacion": observacion,
            "orometro_chipper_inicio": st.session_state.orometro_chipper_inicio,
            "orometro_trituradora_inicio": st.session_state.orometro_trituradora_inicio
        }

        # ENVÍO INMEDIATO A GOOGLE SHEETS
        try:
            res = requests.post(
                WEBHOOK_URL, 
                data=json.dumps(registro_payload), 
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if res.status_code == 200:
                st.session_state.registros.append(registro_payload)
                st.success(f"✅ ¡Guardado en Google Drive! {maquina_sel} - {producto_sel}: {peso_neto_kg:.2f} kg netos ({ahora_ecuador.strftime('%H:%M:%S')} Ecuador)")
            else:
                st.error(f"Error al transmitir a Google Sheets. Código: {res.status_code}")
        except Exception as e:
            st.error(f"Error de conexión con Google Drive: {e}")
    else:
        st.warning("Ingrese un peso bruto superior a 0 kg.")

st.divider()

# 3. TABLA DE REGISTROS DE LA SESIÓN ACTUAL
st.subheader("📊 Registros del Turno en Pantalla")

if len(st.session_state.registros) > 0:
    df = pd.DataFrame(st.session_state.registros)
    columnas_ver = ["hora_corta", "maquina", "producto", "unidades", "peso_bruto_kg", "peso_neto_kg", "observacion"]
    st.dataframe(df[columnas_ver], use_container_width=True)

    neto_chip = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Chipper")
    neto_trit = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Neto Chipper", f"{neto_chip:.2f} kg")
    c2.metric("Neto Trituradora", f"{neto_trit:.2f} kg")
    c3.metric("Total Neto Turno", f"{(neto_chip + neto_trit):.2f} kg")
else:
    st.info("Los registros enviados aparecen inmediatamente en tu archivo de Google Sheets en Drive.")

st.divider()

# 4. CIERRE Y FINALIZACIÓN DE JORNADA
st.subheader("🏁 3. Cierre de Jornada y Orómetros Finales")

with st.expander("🔻 Desplegar para ingresar orómetros finales y cerrar turno"):
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
        
    btn_finalizar_turno = st.button("🔒 GUARDAR RESUMEN Y FINALIZAR JORNADA", use_container_width=True)
    
    if btn_finalizar_turno:
        ahora_fin = datetime.now(ZONA_HORARIA_ECUADOR)
        
        hrs_chipper = round(oro_chip_fin - st.session_state.orometro_chipper_inicio, 2)
        hrs_trituradora = round(oro_trit_fin - st.session_state.orometro_trituradora_inicio, 2)
        
        neto_chip = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Chipper")
        neto_trit = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
        
        rend_chipper = round(neto_chip / hrs_chipper, 2) if hrs_chipper > 0 else 0.0
        rend_trituradora = round(neto_trit / hrs_trituradora, 2) if hrs_trituradora > 0 else 0.0
        
        cierre_payload = {
            "tipo_evento": "FINALIZAR_JORNADA",
            "fecha_inicio": st.session_state.hora_inicio_jornada or ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_fin": ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
            "orometro_inicio_chipper": st.session_state.orometro_chipper_inicio,
            "orometro_fin_chipper": oro_chip_fin,
            "horas_chipper": hrs_chipper,
            "total_peso_chipper_kg": neto_chip,
            "rendimiento_chipper_kg_hr": rend_chipper,
            "orometro_inicio_trituradora": st.session_state.orometro_trituradora_inicio,
            "orometro_fin_trituradora": oro_trit_fin,
            "horas_trituradora": hrs_trituradora,
            "total_peso_trituradora_kg": neto_trit,
            "rendimiento_trituradora_kg_hr": rend_trituradora,
            "peso_total_jornada_kg": neto_chip + neto_trit
        }
        
        try:
            res = requests.post(WEBHOOK_URL, data=json.dumps(cierre_payload), headers={"Content-Type": "application/json"}, timeout=10)
            if res.status_code == 200:
                st.success("🎉 ¡Resumen de jornada y orómetros grabado en Google Drive!")
                
                # Reseteo de pantalla tras enviar el cierre
                st.session_state.registros = []
                st.session_state.orometro_chipper_inicio = 0.0
                st.session_state.orometro_trituradora_inicio = 0.0
                st.session_state.hora_inicio_jornada = None
                
                st.button("🔄 Reiniciar App para Nuevo Turno", on_click=lambda: st.rerun())
            else:
                st.error(f"Error al enviar cierre. Código: {res.status_code}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
