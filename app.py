import streamlit as st
import pandas as pd
import io
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(page_title="Producción Biomasa", page_icon="🪵", layout="wide")

# Opciones de materiales por máquina
MATERIALES = {
    "Trituradora": ["Pallets de madera", "Pallets de plywood", "Canasta de tablas"],
    "Chipper": ["Jampa", "Canasta de despunte", "Bigbag"]
}

# -----------------------------------------------------------------------------
# FUNCIÓN DE CONEXIÓN Y GUARDADO AUTOMÁTICO EN GOOGLE DRIVE (SHEETS)
# -----------------------------------------------------------------------------
def guardar_en_google_drive(fila_datos):
    try:
        # Verificar si existen los secretos
        if "gcp_service_account" not in st.secrets:
            return False, "No se encontró la sección [gcp_service_account] en los Secretos de Streamlit."

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Copiar secretos e interpretar correctamente la clave privada
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Abrir el documento en Drive por su nombre exacto
        sheet = client.open("Control_Produccion_Biomasa").sheet1
        
        # Agregar la fila
        sheet.append_row(fila_datos)
        return True, "Guardado exitosamente en Google Drive."
    except gspread.exceptions.SpreadsheetNotFound:
        return False, "Error: No se encontró la hoja 'Control_Produccion_Biomasa' en Drive. Revisa el nombre exacto del archivo."
    except Exception as e:
        return False, f"Error de conexión con Google: {str(e)}"

# -----------------------------------------------------------------------------
# INICIALIZACIÓN DE ESTADO
# -----------------------------------------------------------------------------
if "jornada_iniciada" not in st.session_state:
    st.session_state["jornada_iniciada"] = False
if "jornada_bloqueada" not in st.session_state:
    st.session_state["jornada_bloqueada"] = False
if "datos_jornada" not in st.session_state:
    st.session_state["datos_jornada"] = {}
if "registros_pesos" not in st.session_state:
    st.session_state["registros_pesos"] = pd.DataFrame(columns=[
        "Hora Registro", "Proceso / Máquina", "Tipo de Material", 
        "Cantidad (Unidades)", "Peso Registrado (Kg)", "Tara Uñas (Kg)", "Peso Neto (Kg)"
    ])
if "ultimo_mensaje" not in st.session_state:
    st.session_state["ultimo_mensaje"] = None

# -----------------------------------------------------------------------------
# MENÚ LATERAL: CONTROL DE JORNADA
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Control de Jornada")

if not st.session_state["jornada_iniciada"]:
    st.sidebar.subheader("1. Apertura de Jornada")
    fecha_jornada = st.sidebar.date_input("Fecha", datetime.now())
    turno_jornada = st.sidebar.selectbox("Turno de Trabajo", ["Turno 1 (Día)", "Turno 2 (Noche)", "Turno 3 (Rotativo)"])
    
    st.sidebar.markdown("**👥 Equipo Trituradora:**")
    tri_1 = st.sidebar.text_input("Integrante 1 (Trituradora)", key="tri_1")
    tri_2 = st.sidebar.text_input("Integrante 2 (Trituradora)", key="tri_2")
    tri_3 = st.sidebar.text_input("Integrante 3 (Trituradora)", key="tri_3")
    
    st.sidebar.markdown("**👥 Equipo Chipper:**")
    chip_1 = st.sidebar.text_input("Integrante 1 (Chipper)", key="chip_1")
    chip_2 = st.sidebar.text_input("Integrante 2 (Chipper)", key="chip_2")
    chip_3 = st.sidebar.text_input("Integrante 3 (Chipper)", key="chip_3")
    
    st.sidebar.markdown("**⏱️ Horómetros de Inicio:**")
    h_init_tri = st.sidebar.number_input("Horómetro Inicio - Trituradora 🪚", min_value=0.0, step=0.1, value=0.0)
    h_init_chip = st.sidebar.number_input("Horómetro Inicio - Chipper 🦫", min_value=0.0, step=0.1, value=0.0)
    
    if st.sidebar.button("🚀 Iniciar Jornada", type="primary", use_container_width=True):
        st.session_state["datos_jornada"] = {
            "Fecha": fecha_jornada.strftime("%Y-%m-%d"),
            "Turno": turno_jornada,
            "Equipo_Trituradora": ", ".join(filter(None, [tri_1, tri_2, tri_3])),
            "Equipo_Chipper": ", ".join(filter(None, [chip_1, chip_2, chip_3])),
            "H_Inicio_Trituradora": h_init_tri,
            "H_Inicio_Chipper": h_init_chip,
            "H_Fin_Trituradora": 0.0,
            "H_Fin_Chipper": 0.0,
            "Horas_Trituradora": 0.0,
            "Horas_Chipper": 0.0
        }
        st.session_state["jornada_iniciada"] = True
        st.session_state["ultimo_mensaje"] = ("success", "✅ Jornada iniciada. Sistema listo.")
        st.rerun()

else:
    info_j = st.session_state["datos_jornada"]
    st.sidebar.success(f"🟢 **JORNADA ACTIVA**\n\n**Fecha:** {info_j['Fecha']}\n**Turno:** {info_j['Turno']}")
    
    if not st.session_state["jornada_bloqueada"]:
        st.sidebar.markdown("---")
        st.sidebar.subheader("2. Cierre de Jornada")
        st.sidebar.markdown("**⏱️ Horómetros Fin:**")
        h_fin_tri = st.sidebar.number_input("Horómetro Fin - Trituradora 🪚", min_value=info_j["H_Inicio_Trituradora"], step=0.1, value=info_j["H_Inicio_Trituradora"])
        h_fin_chip = st.sidebar.number_input("Horómetro Fin - Chipper 🦫", min_value=info_j["H_Inicio_Chipper"], step=0.1, value=info_j["H_Inicio_Chipper"])
        
        if st.sidebar.button("🔒 Terminar Jornada y Bloquear", type="primary", use_container_width=True):
            if h_fin_tri < info_j["H_Inicio_Trituradora"] or h_fin_chip < info_j["H_Inicio_Chipper"]:
                st.sidebar.error("⚠️ El horómetro final no puede ser menor al inicial.")
            else:
                st.session_state["datos_jornada"]["H_Fin_Trituradora"] = h_fin_tri
                st.session_state["datos_jornada"]["H_Fin_Chipper"] = h_fin_chip
                st.session_state["datos_jornada"]["Horas_Trituradora"] = round(h_fin_tri - info_j["H_Inicio_Trituradora"], 2)
                st.session_state["datos_jornada"]["Horas_Chipper"] = round(h_fin_chip - info_j["H_Inicio_Chipper"], 2)
                st.session_state["jornada_bloqueada"] = True
                st.session_state["ultimo_mensaje"] = ("info", "🔒 Jornada terminada y bloqueada.")
                st.rerun()
    else:
        st.sidebar.error("🔒 JORNADA FINALIZADA Y BLOQUEADA")
        if st.sidebar.button("🔄 Reiniciar / Nueva Jornada (Encerar Todo)", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# -----------------------------------------------------------------------------
# ÁREA PRINCIPAL Y MENSAJES DE NOTIFICACIÓN
# -----------------------------------------------------------------------------
st.title("🪵 Control de Producción de Biomasa")

# Mostrar mensaje persistente de la última acción realizada
if st.session_state["ultimo_mensaje"]:
    tipo_msg, texto_msg = st.session_state["ultimo_mensaje"]
    if tipo_msg == "success":
        st.success(texto_msg)
    elif tipo_msg == "warning":
        st.warning(texto_msg)
    elif tipo_msg == "error":
        st.error(texto_msg)
    elif tipo_msg == "info":
        st.info(texto_msg)

if not st.session_state["jornada_iniciada"]:
    st.warning("⚠️ **Jornada no iniciada.** Por favor completa los datos en el menú lateral izquierdo y haz clic en **'Iniciar Jornada'** para comenzar.")

# -----------------------------------------------------------------------------
# FORMULARIO PARA REGISTRO DE PESO
# -----------------------------------------------------------------------------
st.subheader("📝 Registro de Entrada de Pesos")

if st.session_state["jornada_iniciada"] and not st.session_state["jornada_bloqueada"]:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        maquina_sel = st.selectbox("1. Proceso / Máquina", ["Trituradora", "Chipper"], key="maquina_select")
    
    with col2:
        opciones_material = MATERIALES[maquina_sel]
        material_sel = st.selectbox("2. Tipo de Material", opciones_material, key="material_select")
        
    with col3:
        cant_sel = st.number_input("3. Unidades", min_value=1, step=1, value=1, key="cant_input")
        
    with col4:
        peso_sel = st.number_input("4. Peso Balanza (Kg)", min_value=0.0, step=5.0, value=0.0, key="peso_input")
        
    with col5:
        tara_sel = st.number_input("5. Tara Uñas (Kg)", min_value=0.0, step=1.0, value=120.0, key="tara_input")
        
    btn_guardar = st.button("📥 Registrar Peso", type="primary", use_container_width=True)
    
    if btn_guardar:
        if peso_sel <= tara_sel and peso_sel > 0:
            st.session_state["ultimo_mensaje"] = ("error", "⚠️ El Peso Balanza debe ser mayor a la Tara de las uñas (120 Kg).")
            st.rerun()
        elif peso_sel == 0:
            st.session_state["ultimo_mensaje"] = ("error", "⚠️ Por favor ingrese un peso válido registrado por la balanza.")
            st.rerun()
        else:
            peso_neto = round(peso_sel - tara_sel, 2)
            str_hora_auto = datetime.now().strftime("%H:%M:%S")
            info_j = st.session_state["datos_jornada"]
            
            # 1. Guardar en memoria de Streamlit
            nuevo_row = pd.DataFrame([{
                "Hora Registro": str_hora_auto,
                "Proceso / Máquina": maquina_sel,
                "Tipo de Material": material_sel,
                "Cantidad (Unidades)": cant_sel,
                "Peso Registrado (Kg)": peso_sel,
                "Tara Uñas (Kg)": tara_sel,
                "Peso Neto (Kg)": peso_neto
            }])
            st.session_state["registros_pesos"] = pd.concat([st.session_state["registros_pesos"], nuevo_row], ignore_index=True)
            
            # 2. Intentar guardar en Google Drive
            fila_drive = [
                str_hora_auto, maquina_sel, material_sel, cant_sel, 
                peso_sel, tara_sel, peso_neto, info_j.get("Fecha"), info_j.get("Turno")
            ]
            
            exito_drive, msg_drive = guardar_en_google_drive(fila_drive)
            
            if exito_drive:
                st.session_state["ultimo_mensaje"] = ("success", f"✅ Registrado a las {str_hora_auto}: {cant_sel}x {material_sel} | Guardado en Google Drive.")
            else:
                st.session_state["ultimo_mensaje"] = ("error", f"⚠️ Guardado localmente, pero falló en Google Drive. {msg_drive}")
                
            st.rerun()

elif st.session_state["jornada_bloqueada"]:
    st.info("🔒 La jornada está **finalizada y bloqueada**. No se permiten nuevos ingresos.")

st.markdown("---")

# -----------------------------------------------------------------------------
# RESUMEN DE PRODUCCIÓN EN TIEMPO REAL
# -----------------------------------------------------------------------------
st.subheader("📊 Resumen de Producción de la Jornada")

df_actual = st.session_state["registros_pesos"]
info_j = st.session_state.get("datos_jornada", {})

c_tri, c_chip = st.columns(2)

# RESUMEN TRITURADORA
with c_tri:
    st.markdown("### 🪚 Proceso: Trituradora")
    df_tri = df_actual[df_actual["Proceso / Máquina"] == "Trituradora"]
    
    total_peso_tri = df_tri["Peso Neto (Kg)"].sum() if not df_tri.empty else 0.0
    total_unid_tri = df_tri["Cantidad (Unidades)"].sum() if not df_tri.empty else 0
    horas_tri = info_j.get("Horas_Trituradora", 0.0)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Peso Neto (Kg)", f"{total_peso_tri:,.2f}")
    m2.metric("Unidades Total", f"{total_unid_tri}")
    m3.metric("Horas Máquina", f"{horas_tri:.2f} hrs")
    
    st.markdown("**Desglose por Tipo de Material:**")
    base_tri = pd.DataFrame({"Tipo de Material": MATERIALES["Trituradora"]})
    if not df_tri.empty:
        agg_tri = df_tri.groupby("Tipo de Material")[["Cantidad (Unidades)", "Peso Neto (Kg)"]].sum().reset_index()
        tabla_tri = pd.merge(base_tri, agg_tri, on="Tipo de Material", how="left").fillna(0)
    else:
        tabla_tri = base_tri
        tabla_tri["Cantidad (Unidades)"] = 0
        tabla_tri["Peso Neto (Kg)"] = 0.0
        
    tabla_tri["Cantidad (Unidades)"] = tabla_tri["Cantidad (Unidades)"].astype(int)
    st.dataframe(tabla_tri, use_container_width=True, hide_index=True)

# RESUMEN CHIPPER
with c_chip:
    st.markdown("### 🦫 Proceso: Chipper")
    df_chip = df_actual[df_actual["Proceso / Máquina"] == "Chipper"]
    
    total_peso_chip = df_chip["Peso Neto (Kg)"].sum() if not df_chip.empty else 0.0
    total_unid_chip = df_chip["Cantidad (Unidades)"].sum() if not df_chip.empty else 0
    horas_chip = info_j.get("Horas_Chipper", 0.0)
    
    n1, n2, n3 = st.columns(3)
    n1.metric("Peso Neto (Kg)", f"{total_peso_chip:,.2f}")
    n2.metric("Unidades Total", f"{total_unid_chip}")
    n3.metric("Horas Máquina", f"{horas_chip:.2f} hrs")
    
    st.markdown("**Desglose por Tipo de Material:**")
    base_chip = pd.DataFrame({"Tipo de Material": MATERIALES["Chipper"]})
    if not df_chip.empty:
        agg_chip = df_chip.groupby("Tipo de Material")[["Cantidad (Unidades)", "Peso Neto (Kg)"]].sum().reset_index()
        tabla_chip = pd.merge(base_chip, agg_chip, on="Tipo de Material", how="left").fillna(0)
    else:
        tabla_chip = base_chip
        tabla_chip["Cantidad (Unidades)"] = 0
        tabla_chip["Peso Neto (Kg)"] = 0.0
        
    tabla_chip["Cantidad (Unidades)"] = tabla_chip["Cantidad (Unidades)"].astype(int)
    st.dataframe(tabla_chip, use_container_width=True, hide_index=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# DETALLE GENERAL DE REGISTROS Y EXPORTACIÓN A EXCEL (.XLSX)
# -----------------------------------------------------------------------------
st.subheader("📋 Historial de Pesos de la Jornada Actual")

st.dataframe(df_actual, use_container_width=True)

if not df_actual.empty or st.session_state["jornada_bloqueada"]:
    st.markdown("#### 📥 Exportar Reporte de Jornada")
    
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df_actual.to_excel(writer, sheet_name='Registro de Pesos', index=False)
        
        if info_j:
            df_info_jornada = pd.DataFrame([{
                "Fecha": info_j.get("Fecha"),
                "Turno": info_j.get("Turno"),
                "Equipo Trituradora": info_j.get("Equipo_Trituradora"),
                "Equipo Chipper": info_j.get("Equipo_Chipper"),
                "Trituradora Horómetro Inicio": info_j.get("H_Inicio_Trituradora"),
                "Trituradora Horómetro Fin": info_j.get("H_Fin_Trituradora"),
                "Trituradora Horas Operadas": info_j.get("Horas_Trituradora"),
                "Chipper Horómetro Inicio": info_j.get("H_Inicio_Chipper"),
                "Chipper Horómetro Fin": info_j.get("H_Fin_Chipper"),
                "Chipper Horas Operadas": info_j.get("Horas_Chipper")
            }])
            df_info_jornada.to_excel(writer, sheet_name='Datos Jornada y Horómetros', index=False)
            
            tabla_tri.to_excel(writer, sheet_name='Resumen Trituradora', index=False)
            tabla_chip.to_excel(writer, sheet_name='Resumen Chipper', index=False)

    bytes_excel = buffer_excel.getvalue()
    
    st.download_button(
        label="📊 Descargar Reporte Completo en Excel (.xlsx)",
        data=bytes_excel,
        file_name=f"reporte_produccion_biomasa_{info_j.get('Fecha', 'jornada')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
