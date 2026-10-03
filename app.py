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
    page_title="Control de Pesajes y Horómetros",
    page_icon="⚖️",
    layout="centered"
)

# Zona horaria oficial de Ecuador (GMT-5)
ZONA_HORARIA_ECUADOR = zoneinfo.ZoneInfo("America/Guayaquil")

# ---------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE APPS SCRIPT (WEBHOOK)
# ---------------------------------------------------------
# Reemplaza esta URL con la URL de tu WebApp desplegada en Google Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzABRcatXyYEFpFm6s1JWSjZWPYaFrrmCPkxy-4uwXVf0WKtvu2OopLey-VBO76kivk/exec"

# PRODUCTOS POR MÁQUINA EXACTOS
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
# MEMORIA DE SESIÓN (ESTADO LOCAL PERSISTENTE)
# ---------------------------------------------------------
if "registros" not in st.session_state:
    st.session_state.registros = []

if "horometro_chipper_inicio" not in st.session_state:
    st.session_state.horometro_chipper_inicio = 0.0

if "horometro_trituradora_inicio" not in st.session_state:
    st.session_state.horometro_trituradora_inicio = 0.0

if "integrante_1" not in st.session_state:
    st.session_state.integrante_1 = ""

if "integrante_2" not in st.session_state:
    st.session_state.integrante_2 = ""

if "integrante_3" not in st.session_state:
    st.session_state.integrante_3 = ""

if "hora_inicio_jornada" not in st.session_state:
    st.session_state.hora_inicio_jornada = None

# ---------------------------------------------------------
# INTERFAZ PRINCIPAL
# ---------------------------------------------------------
st.title("📋 Control de Producción y Horómetros")

# ---------------------------------------------------------
# 1. INTEGRANTES DEL EQUIPO Y HORÓMETROS INICIALES
# ---------------------------------------------------------
st.subheader("👥 1. Datos del Equipo y Horómetros Iniciales")

st.markdown("**Integrantes del Equipo de Trabajo:**")
col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.session_state.integrante_1 = st.text_input("Integrante 1 (Operador)", value=st.session_state.integrante_1)
with col_i2:
    st.session_state.integrante_2 = st.text_input("Integrante 2", value=st.session_state.integrante_2)
with col_i3:
    st.session_state.integrante_3 = st.text_input("Integrante 3", value=st.session_state.integrante_3)

st.markdown("**Horómetros Iniciales:**")
col_h1, col_h2 = st.columns(2)
with col_h1:
    horo_chip_inic = st.number_input(
        "Horómetro Inicial Chipper (hrs)",
        min_value=0.0,
        value=float(st.session_state.horometro_chipper_inicio),
        step=0.1,
        format="%.1f"
    )
    st.session_state.horometro_chipper_inicio = horo_chip_inic

with col_h2:
    horo_trit_inic = st.number_input(
        "Horómetro Inicial Trituradora (hrs)",
        min_value=0.0,
        value=float(st.session_state.horometro_trituradora_inicio),
        step=0.1,
        format="%.1f"
    )
    st.session_state.horometro_trituradora_inicio = horo_trit_inic

st.divider()

# ---------------------------------------------------------
# 2. INGRESO DE PESADAS (REGISTRO EN TIEMPO REAL)
# ---------------------------------------------------------
st.subheader("⚖️ 2. Ingreso de Pesadas")

# Selección de Máquina
maquina_sel = st.selectbox("Máquina", ["Chipper", "Trituradora"])

# Desplegable dinámico de productos
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

st.info(f"💡 **Peso Neto a registrar:** {peso_neto_kg:.2f} kg (Peso Bruto: {peso_bruto_kg:.2f} kg - Tara: {tara_uñas_kg:.1f} kg)")

btn_guardar_pesada = st.button("➕ REGISTRAR PESO (ENVIAR A DRIVE)", use_container_width=True, type="primary")

if btn_guardar_pesada:
    if peso_bruto_kg > 0:
        if not st.session_state.integrante_1.strip():
            st.warning("Por favor ingrese al menos el nombre del Integrante 1 antes de registrar pesadas.")
        else:
            ahora_ecuador = datetime.now(ZONA_HORARIA_ECUADOR)
            
            if st.session_state.hora_inicio_jornada is None:
                st.session_state.hora_inicio_jornada = ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S")

            registro_payload = {
                "tipo_evento": "REGISTRO_PESO",
                "fecha_hora": ahora_ecuador.strftime("%Y-%m-%d %H:%M:%S"),
                "hora_corta": ahora_ecuador.strftime("%H:%M:%S"),
                "integrante_1": st.session_state.integrante_1,
                "integrante_2": st.session_state.integrante_2,
                "integrante_3": st.session_state.integrante_3,
                "maquina": maquina_sel,
                "producto": producto_sel,
                "unidades": int(unidades),
                "peso_bruto_kg": float(peso_bruto_kg),
                "tara_kg": float(tara_uñas_kg),
                "peso_neto_kg": float(peso_neto_kg),
                "horometro_chipper_inicio": st.session_state.horometro_chipper_inicio,
                "horometro_trituradora_inicio": st.session_state.horometro_trituradora_inicio
            }

            # Transmisión inmediata a Google Sheets
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

# ---------------------------------------------------------
# 3. MUESTRA DE REGISTROS DEL TURNO
# ---------------------------------------------------------
st.subheader("📊 Registros del Turno")

if len(st.session_state.registros) > 0:
    df = pd.DataFrame(st.session_state.registros)
    columnas_ver = ["hora_corta", "maquina", "producto", "unidades", "peso_bruto_kg", "tara_kg", "peso_neto_kg"]
    st.dataframe(df[columnas_ver], use_container_width=True)

    neto_chip = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Chipper")
    neto_trit = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Neto Chipper", f"{neto_chip:.2f} kg")
    c2.metric("Neto Trituradora", f"{neto_trit:.2f} kg")
    c3.metric("Total Neto Turno", f"{(neto_chip + neto_trit):.2f} kg")
else:
    st.info("Cada peso guardado se almacena automáticamente en tu hoja de Google Drive.")

st.divider()

# ---------------------------------------------------------
# 4. CIERRE Y FINALIZACIÓN DE JORNADA
# ---------------------------------------------------------
st.subheader("🏁 3. Cierre de Jornada y Horómetros Finales")

with st.expander("🔻 Desplegar para ingresar horómetros finales y cerrar turno"):
    col_fh1, col_fh2 = st.columns(2)
    
    with col_fh1:
        horo_chip_fin = st.number_input(
            "Horómetro Final Chipper (hrs)",
            min_value=st.session_state.horometro_chipper_inicio,
            value=st.session_state.horometro_chipper_inicio,
            step=0.1,
            format="%.1f"
        )
        
    with col_fh2:
        horo_trit_fin = st.number_input(
            "Horómetro Final Trituradora (hrs)",
            min_value=st.session_state.horometro_trituradora_inicio,
            value=st.session_state.horometro_trituradora_inicio,
            step=0.1,
            format="%.1f"
        )
        
    btn_finalizar_turno = st.button("🔒 GUARDAR RESUMEN Y FINALIZAR JORNADA", use_container_width=True)
    
    if btn_finalizar_turno:
        ahora_fin = datetime.now(ZONA_HORARIA_ECUADOR)
        
        hrs_chipper = round(horo_chip_fin - st.session_state.horometro_chipper_inicio, 2)
        hrs_trituradora = round(horo_trit_fin - st.session_state.horometro_trituradora_inicio, 2)
        
        neto_chip = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Chipper")
        neto_trit = sum(r["peso_neto_kg"] for r in st.session_state.registros if r["maquina"] == "Trituradora")
        
        rend_chipper = round(neto_chip / hrs_chipper, 2) if hrs_chipper > 0 else 0.0
        rend_trituradora = round(neto_trit / hrs_trituradora, 2) if hrs_trituradora > 0 else 0.0
        
        cierre_payload = {
            "tipo_evento": "FINALIZAR_JORNADA",
            "fecha_inicio": st.session_state.hora_inicio_jornada or ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_fin": ahora_fin.strftime("%Y-%m-%d %H:%M:%S"),
            "integrante_1": st.session_state.integrante_1,
            "integrante_2": st.session_state.integrante_2,
            "integrante_3": st.session_state.integrante_3,
            "horometro_inicio_chipper": st.session_state.horometro_chipper_inicio,
            "horometro_fin_chipper": horo_chip_fin,
            "horas_chipper": hrs_chipper,
            "total_peso_chipper_kg": neto_chip,
            "rendimiento_chipper_kg_hr": rend_chipper,
            "horometro_inicio_trituradora": st.session_state.horometro_trituradora_inicio,
            "horometro_fin_trituradora": horo_trit_fin,
            "horas_trituradora": hrs_trituradora,
            "total_peso_trituradora_kg": neto_trit,
            "rendimiento_trituradora_kg_hr": rend_trituradora,
            "peso_total_jornada_kg": neto_chip + neto_trit
        }
        
        try:
            res = requests.post(WEBHOOK_URL, data=json.dumps(cierre_payload), headers={"Content-Type": "application/json"}, timeout=10)
            if res.status_code == 200:
                st.success("🎉 ¡Resumen de jornada y horómetros grabado en Google Drive!")
                
                # Reseteo de pantalla
                st.session_state.registros = []
                st.session_state.horometro_chipper_inicio = 0.0
                st.session_state.horometro_trituradora_inicio = 0.0
                st.session_state.integrante_1 = ""
                st.session_state.integrante_2 = ""
                st.session_state.integrante_3 = ""
                st.session_state.hora_inicio_jornada = None
                
                st.button("🔄 Reiniciar App para Nuevo Turno", on_click=lambda: st.rerun())
            else:
                st.error(f"Error al enviar cierre. Código: {res.status_code}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
