import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(page_title="Producción Biomasa", page_icon="🪵", layout="wide")

# Archivos de base de datos local
ARCHIVO_CARGAS = "registro_cargas_biomasa.csv"
ARCHIVO_JORNADAS = "registro_jornadas_biomasa.csv"

# Opciones de productos por tipo de máquina
PRODUCTOS_PROCESO = {
    "Trituradora": [
        "Pallets de madera",
        "Pallets de plywood",
        "Canasta de tablas"
    ],
    "Chipper": [
        "Jampa",
        "Canasta de despunte",
        "Bigbag"
    ]
}

# Carga de datos
def cargar_cargas():
    columnas = ["Fecha", "Turno", "Proceso / Máquina", "Tipo de Material", "Cantidad (Unidades)", "Peso Registrado (Kg)", "Tara Uñas (Kg)", "Peso Neto (Kg)"]
    if os.path.exists(ARCHIVO_CARGAS):
        return pd.read_csv(ARCHIVO_CARGAS)
    return pd.DataFrame(columns=columnas)

def cargar_jornadas():
    columnas = [
        "Fecha", "Turno", 
        "Equipo Trituradora", "Equipo Chipper",
        "Trituradora H.Inicio", "Trituradora H.Fin", "Trituradora Horas",
        "Chipper H.Inicio", "Chipper H.Fin", "Chipper Horas"
    ]
    if os.path.exists(ARCHIVO_JORNADAS):
        return pd.read_csv(ARCHIVO_JORNADAS)
    return pd.DataFrame(columns=columnas)

# Inicialización de estado
if "form_key" not in st.session_state:
    st.session_state["form_key"] = 0
if "jornada_cerrada" not in st.session_state:
    st.session_state["jornada_cerrada"] = False

df_cargas = cargar_cargas()
df_jornadas = cargar_jornadas()

# -----------------------------------------------------------------------------
# 1. MENÚ LATERAL PLEGABLE (DATOS Y HORÓMETROS)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Control de Jornada")
    
    with st.expander("📌 Datos de Jornada y Equipos", expanded=True):
        fecha_jornada = st.date_input("Fecha", datetime.now())
        turno_jornada = st.selectbox("Turno de Trabajo", ["Turno 1 (Día)", "Turno 2 (Noche)", "Turno 3 (Rotativo)"])
        
        st.markdown("---")
        st.markdown("**👥 Equipo Trituradora:**")
        tri_1 = st.text_input("Integrante 1 (Trituradora)")
        tri_2 = st.text_input("Integrante 2 (Trituradora)")
        tri_3 = st.text_input("Integrante 3 (Trituradora)")
        
        st.markdown("---")
        st.markdown("**👥 Equipo Chipper:**")
        chip_1 = st.text_input("Integrante 1 (Chipper)")
        chip_2 = st.text_input("Integrante 2 (Chipper)")
        chip_3 = st.text_input("Integrante 3 (Chipper)")

    with st.expander("⏱️ Horómetros (Inicio y Fin)", expanded=True):
        st.markdown("**Máquina Trituradora:**")
        tri_h_inicio = st.number_input("Horómetro Inicio - Trituradora", min_value=0.0, step=0.1, value=0.0)
        tri_h_fin = st.number_input("Horómetro Fin - Trituradora", min_value=0.0, step=0.1, value=0.0)
        horas_tri_calc = max(0.0, round(tri_h_fin - tri_h_inicio, 2)) if tri_h_fin >= tri_h_inicio else 0.0
        st.caption(f"⏱️ Horas operadas Trituradora: **{horas_tri_calc} hrs**")
        
        st.markdown("---")
        st.markdown("**Máquina Chipper:**")
        chip_h_inicio = st.number_input("Horómetro Inicio - Chipper", min_value=0.0, step=0.1, value=0.0)
        chip_h_fin = st.number_input("Horómetro Fin - Chipper", min_value=0.0, step=0.1, value=0.0)
        horas_chip_calc = max(0.0, round(chip_h_fin - chip_h_inicio, 2)) if chip_h_fin >= chip_h_inicio else 0.0
        st.caption(f"⏱️ Horas operadas Chipper: **{horas_chip_calc} hrs**")
        
        st.markdown("---")
        
        if not st.session_state["jornada_cerrada"]:
            if st.button("🔒 Cerrar Jornada y Bloquear Registros", type="primary", use_container_width=True):
                if tri_h_fin < tri_h_inicio or chip_h_fin < chip_h_inicio:
                    st.error("⚠️ El horómetro final no puede ser menor al horómetro inicial.")
                else:
                    eq_tri = ", ".join(filter(None, [tri_1, tri_2, tri_3]))
                    eq_chip = ", ".join(filter(None, [chip_1, chip_2, chip_3]))
                    
                    nueva_jornada = pd.DataFrame([{
                        "Fecha": fecha_jornada.strftime("%Y-%m-%d"),
                        "Turno": turno_jornada,
                        "Equipo Trituradora": eq_tri,
                        "Equipo Chipper": eq_chip,
                        "Trituradora H.Inicio": tri_h_inicio,
                        "Trituradora H.Fin": tri_h_fin,
                        "Trituradora Horas": horas_tri_calc,
                        "Chipper H.Inicio": chip_h_inicio,
                        "Chipper H.Fin": chip_h_fin,
                        "Chipper Horas": horas_chip_calc
                    }])
                    
                    df_j = pd.concat([cargar_jornadas(), nueva_jornada], ignore_index=True)
                    df_j.to_csv(ARCHIVO_JORNADAS, index=False)
                    st.session_state["jornada_cerrada"] = True
                    st.success("✅ Jornada cerrada con éxito.")
                    st.rerun()
        else:
            st.warning("🔒 JORNADA CERRADA")
            if st.button("🔓 Reabrir Jornada para Nuevos Registros", use_container_width=True):
                st.session_state["jornada_cerrada"] = False
                st.rerun()

# -----------------------------------------------------------------------------
# 2. ÁREA PRINCIPAL
# -----------------------------------------------------------------------------
st.title("🪵 Control de Producción de Biomasa")

# REGISTRO DE PESOS ENTRANTES
st.subheader("📝 Registro de Entrada de Pesos")

if st.session_state["jornada_cerrada"]:
    st.error("🔒 La jornada ha sido cerrada con la lectura de horómetros finales. No se permiten más registros de pesos. Si requieres ingresar algo más, desbloquea la jornada desde el menú lateral.")
else:
    with st.form(key=f"form_pesos_{st.session_state['form_key']}"):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            maquina_input = st.selectbox("1. Máquina / Proceso", list(PRODUCTOS_PROCESO.keys()))
            
        with col2:
            materiales_opciones = PRODUCTOS_PROCESO[maquina_input]
            material_input = st.selectbox("2. Tipo de Material", materiales_opciones)
            
        with col3:
            cantidad_input = st.number_input("3. Cantidad Unidades", min_value=1, step=1, value=1)
            
        with col4:
            peso_input = st.number_input("4. Peso Registrado (Kg)", min_value=0.0, step=5.0, value=0.0)
            
        with col5:
            tara_input = st.number_input("5. Tara Uñas (Kg)", min_value=0.0, step=1.0, value=120.0)
            
        btn_registrar = st.form_submit_button("📥 Registrar Peso", type="primary", use_container_width=True)

    if btn_registrar:
        if peso_input <= tara_input and peso_input > 0:
            st.error("⚠️ El peso registrado en el montacargas debe ser mayor a la tara de las uñas (120 Kg).")
        elif peso_input == 0:
            st.error("⚠️ Ingrese el peso capturado en el montacargas.")
        else:
            peso_neto = max(0.0, peso_input - tara_input)
            
            nuevo_registro = pd.DataFrame([{
                "Fecha": fecha_jornada.strftime("%Y-%m-%d"),
                "Turno": turno_jornada,
                "Proceso / Máquina": maquina_input,
                "Tipo de Material": material_input,
                "Cantidad (Unidades)": cantidad_input,
                "Peso Registrado (Kg)": peso_input,
                "Tara Uñas (Kg)": tara_input,
                "Peso Neto (Kg)": peso_neto
            }])
            
            df_cargas_actualizado = pd.concat([df_cargas, nuevo_registro], ignore_index=True)
            df_cargas_actualizado.to_csv(ARCHIVO_CARGAS, index=False)
            
            st.session_state["form_key"] += 1
            st.success(f"✅ Registrado: {cantidad_input}x {material_input} en {maquina_input} | Peso Neto: {peso_neto:.2f} Kg")
            st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. RESUMEN DE PRODUCCIÓN POR MÁQUINA
# -----------------------------------------------------------------------------
st.subheader("📊 Resumen de Producción por Máquina")

df_cargas = cargar_cargas()

col_m1, col_m2 = st.columns(2)

# RESUMEN TRITURADORA
with col_m1:
    st.markdown("### ⚙️ Máquina Trituradora")
    df_tri = df_cargas[df_cargas["Proceso / Máquina"] == "Trituradora"]
    
    peso_tri_total = df_tri["Peso Neto (Kg)"].sum() if not df_tri.empty else 0.0
    st.metric("Peso Neto Total (Kg)", f"{peso_tri_total:,.2f}")
    st.metric("Horas Operadas del Turno", f"{horas_tri_calc:.2f} hrs")
    
    st.markdown("**Unidades Procesadas por Material:**")
    if not df_tri.empty:
        resumen_tri = df_tri.groupby("Tipo de Material")[["Cantidad (Unidades)", "Peso Neto (Kg)"]].sum().reset_index()
        st.dataframe(resumen_tri, use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros para Trituradora.")

# RESUMEN CHIPPER
with col_m2:
    st.markdown("### ⚙️ Máquina Chipper")
    df_chip = df_cargas[df_cargas["Proceso / Máquina"] == "Chipper"]
    
    peso_chip_total = df_chip["Peso Neto (Kg)"].sum() if not df_chip.empty else 0.0
    st.metric("Peso Neto Total (Kg)", f"{peso_chip_total:,.2f}")
    st.metric("Horas Operadas del Turno", f"{horas_chip_calc:.2f} hrs")
    
    st.markdown("**Unidades Procesadas por Material:**")
    if not df_chip.empty:
        resumen_chip = df_chip.groupby("Tipo de Material")[["Cantidad (Unidades)", "Peso Neto (Kg)"]].sum().reset_index()
        st.dataframe(resumen_chip, use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros para Chipper.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. HOJA DE DATOS GENERAL Y FILTROS (ESTILO EXCEL)
# -----------------------------------------------------------------------------
st.subheader("📋 Registro Detallado y Exportación")

if df_cargas.empty:
    st.info("No hay registros almacenados todavía.")
else:
    # Filtros
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        filtro_maquina = st.multiselect("Filtrar por Máquina:", options=df_cargas["Proceso / Máquina"].unique(), default=df_cargas["Proceso / Máquina"].unique())
    with f_col2:
        filtro_material = st.multiselect("Filtrar por Material:", options=df_cargas["Tipo de Material"].unique(), default=df_cargas["Tipo de Material"].unique())
        
    df_filtrado = df_cargas[
        (df_cargas["Proceso / Máquina"].isin(filtro_maquina)) &
        (df_cargas["Tipo de Material"].isin(filtro_material))
    ]
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Exportar datos
    exp_col1, exp_col2 = st.columns(2)
    
    with exp_col1:
        csv_cargas = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Registro de Pesos (CSV)",
            data=csv_cargas,
            file_name=f"pesos_biomasa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    with exp_col2:
        df_jornadas_todas = cargar_jornadas()
        if not df_jornadas_todas.empty:
            csv_jornadas = df_jornadas_todas.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte de Horómetros y Jornadas (CSV)",
                data=csv_jornadas,
                file_name=f"jornadas_horometros_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
