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
    page_title="Control de Pesajes y Producción",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Zona horaria oficial de Ecuador (GMT-5)
ZONA_HORARIA_ECUADOR = zoneinfo.ZoneInfo("America/Guayaquil")

# ---------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE APPS SCRIPT (WEBHOOK)
# ---------------------------------------------------------
# Reemplaza esta URL con la URL de tu WebApp desplegada en Google Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/TU_SCRIPT_ID_AQUI/exec"

# PRODUCTOS PERMITIDOS POR MÁQUINA
PRODUCTOS_POR_MAQUINA = {
    "Chipper": [
        "Jampa",
        "Canasta de despunte",
        "Bigbag"
    ],
    "Trituradora": [
        "Pallets de madera",
        "Pallets de plywood",
        "Canasta de tablas"
    ]
}

# ---------------------------------------------------------
# MEMORIA DE SESIÓN (PERSISTENCIA LOCAL)
# ---------------------------------------------------------
if "registros" not in st.session_state:
    st.session_state.registros = []

if "horometro_chipper_inicio" not in st.session_state:
    st.session_state.horometro_chipper_inicio = 0.0

if "horometro_trituradora_inicio" not in st.session_state:
    st.session_state.horometro_trituradora_inicio = 0.0

# Equipo Chipper (3 Integrantes)
if "chip_int_1" not in st.session_state:
    st.session_state.chip_int_1 = ""
if "chip_int_2" not in st.session_state:
    st.session_state.chip_int_2 = ""
if "chip_int_3" not in st.session_state:
    st.session_state.chip_int_3 = ""

# Equipo Trituradora (3 Integrantes)
if "trit_int_1" not in st.session_state:
    st.session_state.trit_int_1 = ""
if "trit_int_2" not in st.session_state:
    st.session_state.trit_int_2 = ""
if "trit_int_3" not in st.session_state:
    st.session_state.trit_int_3 = ""

if "turno" not in st.session_state:
    st.session_state.turno = "Diurno"

if "hora_inicio_jornada" not in st.session_state:
    st.session_state.hora_inicio_jornada = None

# ---------------------------------------------------------
# MENÚ LATERAL (SIDEBAR) - CONFIGURACIÓN DE EQUIPOS Y TURNO
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuración del Turno")
    
    # 1. Turno de trabajo
    st.subheader("🕒 Turno de Trabajo")
    turno_sel = st.selectbox("Seleccione Turno", ["Diurno", "Nocturno"], key="input_turno")
    st.session_state.turno = turno_sel
    
    st.divider()
    
    # 2. Equipo Chipper
    st.subheader("🌲 Equipo Chipper")
    st.session_state.chip_int_1 = st.text_input("Integrante 1 (Operador)", value=st.session_state.chip_int_1, key="input_chip_1")
    st.session_state.chip_int_2 = st.text_input("Integrante 2", value=st.session_state.chip_int_2, key="input_chip_2")
    st.session_state.chip_int_3 = st.text_input("Integrante 3", value=st.session_state.chip_int_3, key="input_chip_3")
    
    st.divider()
    
    # 3. Equipo Trituradora
    st.subheader("⚙️ Equipo Trituradora")
    st.session_state.trit_int_1 = st.text_input("Integrante 1 (Operador)", value=st.session_state.trit_int_1, key="input_trit_1")
    st.session_state.trit_int_2 = st.text_input("Integrante 2", value=st.session_state.trit_int_2, key="input_trit_2")
    st.session_state.trit_int_3 = st.text_input("Integrante 3", value=st.session_state.trit_int_3, key="input_trit_3")
    
    st.divider()
    
    # 4. Horómetros Iniciales
    st.subheader("⏱️ Horómetros Iniciales")
    h_chip_init = st.number_input("Horómetro Inic. Chipper (hrs)", min_value=0.0, value=float(st.session_state.horometro_chipper_inicio), step=0.1, format="%.1f", key="input_h_chip_init")
    st.session_state.horometro_chipper_inicio = h_chip_init
    
    h_trit_init = st.number_input("Horómetro Inic. Trituradora (hrs)", min_value=0.0, value=float(st.session_state.horometro_trituradora_inicio), step=0.1, format="%.1f", key="input_h_trit_init")
    st.session_state.horometro_trituradora_inicio = h_trit_init

    st.divider()
    
    # 5. Horómetros Finales y Cierre de Jornada
    st.subheader("🏁 Cierre de Jornada")
    with st.expander("Ingresar Horómetros Finales"):
        h_chip_fin = st.number_input("Horómetro Fin Chipper", min_value=st.session_state.horometro_chipper_inicio, value=st.session_state.horometro_chipper_inicio, step=0.1, format="%.1f", key="input_h_chip_fin")
        h_trit_fin = st.number_input("Horómetro Fin Trituradora", min_value=st.session_state.horometro_trituradora_inicio, value=st.session_state.horometro_trituradora_inicio, step=0.1, format="%.1f", key="input_h_trit_fin")
        
        btn_cierre = st.button("🔒 FINALIZAR Y ENVIAR JORNADA", use_container_width=True)
        
        if btn_cierre:
            ahora_fin = datetime.now(ZONA_HORARIA_ECUADOR)
            
            hrs_chipper = round(h_chip_fin - st.session_state.horometro_chipper_inicio, 2)
            hrs_trituradora = round(h_trit_fin - st.session_state.horometro_trituradora_inicio, 2)
            
            neto_chip = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Chipper")
            neto_trit = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
            
            rend_chipper = round(neto_chip / hrs_chipper, 2) if hrs_chipper > 0 else 0.0
            rend_trituradora = round(neto_trit / hrs_trituradora, 2) if hrs_trituradora > 0 else 0.0
            
            cierre_payload = {
                "tipo_evento": "FINALIZAR_JORNADA",
                "fecha_inicio": st.session_state.hora_inicio_jornada or ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
                "fecha_fin": ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
                "turno": st.session_state.turno,
                "chip_int_1": st.session_state.chip_int_1,
                "chip_int_2": st.session_state.chip_int_2,
                "chip_int_3": st.session_state.chip_int_3,
                "trit_int_1": st.session_state.trit_int_1,
                "trit_int_2": st.session_state.trit_int_2,
                "trit_int_3": st.session_state.trit_int_3,
                "horometro_inicio_chipper": st.session_state.horometro_chipper_inicio,
                "horometro_fin_chipper": h_chip_fin,
                "horas_chipper": hrs_chipper,
                "total_peso_chipper_kg": neto_chip,
                "rendimiento_chipper_kg_hr": rend_chipper,
                "horometro_inicio_trituradora": st.session_state.horometro_trituradora_inicio,
                "horometro_fin_trituradora": h_trit_fin,
                "horas_trituradora": hrs_trituradora,
                "total_peso_trituradora_kg": neto_trit,
                "rendimiento_trituradora_kg_hr": rend_trituradora,
                "peso_total_jornada_kg": neto_chip + neto_trit
            }
            
            try:
                res = requests.post(WEBHOOK_URL, data=json.dumps(cierre_payload), headers={"Content-Type": "application/json"}, timeout=10)
                if res.status_code == 200:
                    st.success("🎉 Cierre de jornada guardado exitosamente en Google Drive")
                    st.session_state.registros = []
                    st.session_state.horometro_chipper_inicio = 0.0
                    st.session_state.horometro_trituradora_inicio = 0.0
                    st.session_state.chip_int_1 = ""
                    st.session_state.chip_int_2 = ""
                    st.session_state.chip_int_3 = ""
                    st.session_state.trit_int_1 = ""
                    st.session_state.trit_int_2 = ""
                    st.session_state.trit_int_3 = ""
                    st.session_state.hora_inicio_jornada = None
                    st.rerun()
                else:
                    st.error(f"Error al enviar cierre. Código: {res.status_code}")
            except Exception as e:
                st.error(f"Error de conexión con Google Drive: {e}")

# ---------------------------------------------------------
# INTERFAZ PRINCIPAL - INGRESO DE PESADAS Y CONTROL EN VIVO
# ---------------------------------------------------------
st.title("📋 Control de Pesajes y Producción (Tiempo Real)")

# Resumen rápido del estado configurado en el panel izquierdo
c_t1, c_t2, c_t3 = st.columns(3)
with c_t1:
    st.info(f"🕒 **Turno:** {st.session_state.turno}")
with c_t2:
    st.info(f"🌲 **Op. Chipper:** {st.session_state.chip_int_1 or 'No asignado'}")
with c_t3:
    st.info(f"⚙️ **Op. Trituradora:** {st.session_state.trit_int_1 or 'No asignado'}")

st.subheader("⚖️ Ingreso de Pesadas")

col_m, col_p = st.columns(2)
with col_m:
    maquina_sel = st.selectbox("Máquina", ["Chipper", "Trituradora"])
with col_p:
    producto_sel = st.selectbox("Producto", PRODUCTOS_POR_MAQUINA[maquina_sel])

col_u, col_pb, col_t = st.columns(3)
with col_u:
    unidades = st.number_input("Cantidad / Unidades", min_value=1, step=1, value=1)
with col_pb:
    peso_bruto_kg = st.number_input("Peso Bruto (kg)", min_value=0.0, step=0.5, format="%.2f")
with col_t:
    tara_uñas_kg = st.number_input("Tara Uñas (kg)", min_value=0.0, value=120.0, step=1.0, format="%.1f")

# Cálculo automático de Peso Neto
peso_neto_kg = max(0.0, peso_bruto_kg - tara_uñas_kg) if peso_bruto_kg > 0 else 0.0

st.info(f"💡 **Peso Neto:** {peso_neto_kg:.2f} kg (Peso Bruto: {peso_bruto_kg:.2f} kg - Tara: {tara_uñas_kg:.1f} kg)")

btn_guardar_pesada = st.button("➕ REGISTRAR PESO (ENVIAR A DRIVE)", use_container_width=True, type="primary")

if btn_guardar_pesada:
    if peso_bruto_kg > 0:
        # Validación: al menos el operador principal de la máquina seleccionada
        op_actual = st.session_state.chip_int_1 if maquina_sel == "Chipper" else st.session_state.trit_int_1
        
        if not op_actual.strip():
            st.warning(f"Por favor despliega el menú lateral 👈 e ingresa al menos el Integrante 1 (Operador) del equipo {maquina_sel}.")
        else:
            ahora_ecuador = datetime.now(ZONA_HORARIA_ECUADOR)
            
            if st.session_state.hora_inicio_jornada is None:
                st.session_state.hora_inicio_jornada = ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S")

            registro_payload = {
                "tipo_evento": "REGISTRO_PESO",
                "fecha_hora": ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S"),
                "hora_corta": ahora_ecuador.strftime("%H:%M:%S"),
                "turno": st.session_state.turno,
                "maquina": maquina_sel,
                "producto": producto_sel,
                "unidades": int(unidades),
                "peso_bruto_kg": float(peso_bruto_kg),
                "tara_kg": float(tara_uñas_kg),
                "peso_neto_kg": float(peso_neto_kg),
                "chip_int_1": st.session_state.chip_int_1,
                "chip_int_2": st.session_state.chip_int_2,
                "chip_int_3": st.session_state.chip_int_3,
                "trit_int_1": st.session_state.trit_int_1,
                "trit_int_2": st.session_state.trit_int_2,
                "trit_int_3": st.session_state.trit_int_3,
                "horometro_chipper_inicio": st.session_state.horometro_chipper_inicio,
                "horometro_trituradora_inicio": st.session_state.horometro_trituradora_inicio
            }

            # Envió instantáneo a Google Sheets
            try:
                res = requests.post(
                    WEBHOOK_URL, 
                    data=json.dumps(registro_payload), 
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if res.status_code == 200:
                    st.session_state.registros.append(registro_payload)
                    st.success(f"✅ ¡Pesada guardada en Google Drive! {maquina_sel} - {producto_sel}: {peso_neto_kg:.2f} kg netos ({ahora_ecuador.strftime('%H:%M:%S')} Ecuador)")
                else:
                    st.error(f"Error al transmitir a Google Drive. Código HTTP: {res.status_code}")
            except Exception as e:
                st.error(f"Error de conexión con Google Drive: {e}")
    else:
        st.warning("Ingrese un peso bruto superior a 0 kg.")

st.divider()

# ---------------------------------------------------------
# TABLA Y RESUMEN EN VIVO DE REGISTROS
# ---------------------------------------------------------
st.subheader("📊 Registros del Turno")

if len(st.session_state.registros) > 0:
    df = pd.DataFrame(st.session_state.registros)
    columnas_ver = ["hora_corta", "turno", "maquina", "producto", "unidades", "peso_bruto_kg", "tara_kg", "peso_neto_kg"]
    st.dataframe(df[columnas_ver], use_container_width=True)

    neto_chip = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Chipper")
    neto_trit = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Neto Chipper", f"{neto_chip:.2f} kg")
    c2.metric("Neto Trituradora", f"{neto_trit:.2f} kg")
    c3.metric("Total Neto Turno", f"{(neto_chip + neto_trit):.2f} kg")
else:
    st.info("💡 Usa el menú lateral desplegable 👈 para configurar Turno, Integrantes del Equipo y Horómetros Iniciales. Los pesos registrados se guardan automáticamente en tu Google Drive.")
