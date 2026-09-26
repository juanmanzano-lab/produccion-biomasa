import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración inicial de la pantalla
st.set_page_config(page_title="Producción Biomasa", page_icon="🪵", layout="wide")

# Archivos de base de datos
ARCHIVO_CARGAS = "registro_cargas_biomasa.csv"
ARCHIVO_JORNADAS = "registro_jornadas_biomasa.csv"

# Opciones de productos por tipo de máquina
PRODUCTOS_PROCESO = {
    "Trituradora": [
        "Pallets de madera",
        "Canasta de tablas",
        "Pallets de plywood"
    ],
    "Chipper": [
        "Jampa",
        "Canasta de despunte",
        "Tula de desperdicio"
    ]
}

# Carga de archivos CSV
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

# Inicializar clave de formulario para limpiar campos tras registro
if "form_key" not in st.session_state:
    st.session_state["form_key"] = 0

# -----------------------------------------------------------------------------
# 1. MENÚ IZQUIERDO PLEGABLE (CONFIGURACIÓN DE JORNADA Y HORÓMETROS)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Control de Jornada")
    
    with st.expander("📌 Datos de Jornada y Equipos", expanded=True):
        fecha_jornada = st.date_input("Fecha", datetime.now())
        turno_jornada = st.selectbox("Turno de Trabajo", ["Turno 1 (Día)", "Turno 2 (Noche)", "Turno 3 (Rotativo)"])
        
        st.markdown("---")
        st.markdown("**👥 Equipo Trituradora:**")
        integrante_tri_1 = st.text_input("Integrante 1 (Trituradora)", placeholder="Nombre integrante 1")
        integrante_tri_2 = st.text_input("Integrante 2 (Trituradora)", placeholder="Nombre integrante 2")
        integrante_tri_3 = st.text_input("Integrante 3 (Trituradora)", placeholder="Nombre integrante 3")
        
        st.markdown("---")
        st.markdown("**👥 Equipo Chipper:**")
        integrante_chip_1 = st.text_input("Integrante 1 (Chipper)", placeholder="Nombre integrante 1")
        integrante_chip_2 = st.text_input("Integrante 2 (Chipper)", placeholder="Nombre integrante 2")
        integrante_chip_3 = st.text_input("Integrante 3 (Chipper)", placeholder="Nombre integrante 3")

    with st.expander("⏱️ Horómetros (Inicio / Fin)", expanded=True):
        st.markdown("**Trituradora:**")
        tri_h_inicio = st.number_input("Horómetro Inicio (Trituradora)", min_value=0.0, step=0.1, value=0.0)
        tri_h_fin = st.number_input("Horómetro Fin (Trituradora)", min_value=0.0, step=0.1, value=0.0)
        
        st.markdown("**Chipper:**")
        chip_h_inicio = st.number_input("Horómetro Inicio (Chipper)", min_value=0.0, step=0.1, value=0.0)
        chip_h_fin = st.number_input("Horómetro Fin (Chipper)", min_value=0.0, step=0.1, value=0.0)
        
        if st.button("🔒 Guardar y Cerrar Jornada", type="secondary", use_container_width=True):
            if tri_h_fin < tri_h_inicio or chip_h_fin < chip_h_inicio:
                st.error("⚠️ El horómetro final no puede ser menor al inicial.")
            else:
                eq_tri = ", ".join(filter(None, [integrante_tri_1, integrante_tri_2, integrante_tri_3]))
                eq_chip = ", ".join(filter(None, [integrante_chip_1, integrante_chip_2, integrante_chip_3]))
                
                horas_tri = round(tri_h_fin - tri_h_inicio, 2)
                horas_chip = round(chip_h_fin - chip_h_inicio, 2)
                
                nueva_jornada = pd.DataFrame([{
                    "Fecha": fecha_jornada.strftime("%Y-%m-%d"),
                    "Turno": turno_jornada,
                    "Equipo Trituradora": eq_tri,
                    "Equipo Chipper": eq_chip,
                    "Trituradora H.Inicio": tri_h_inicio,
                    "Trituradora H.Fin": tri_h_fin,
                    "Trituradora Horas": horas_tri,
                    "Chipper H.Inicio": chip_h_inicio,
                    "Chipper H.Fin": chip_h_fin,
                    "Chipper Horas": horas_chip
                }])
                
                df_j = pd.concat([cargar_jornadas(), nueva_jornada], ignore_index=True)
                df_j.to_csv(ARCHIVO_JORNADAS, index=False)
                st.success("✅ Jornada y horómetros guardados con éxito.")

# -----------------------------------------------------------------------------
# 2. ÁREA PRINCIPAL
# -----------------------------------------------------------------------------
st.title("🪵 Control de Producción de Biomasa")

df_cargas = cargar_cargas()

# RESUMEN ACUMULADO
st.subheader("📊 Resumen Acumulado de Producción")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Peso Neto Total Acumulado (Kg)", f"{df_cargas['Peso Neto (Kg)'].sum():,.2f}")
kpi2.metric("Total Unidades Registradas", f"{int(df_cargas['Cantidad (Unidades)'].sum()):,}")
kpi3.metric("Total de Registros de Pesos", len(df_cargas))

st.markdown("---")

# FORMULARIO HORIZONTAL PARA REGISTRO DE PESO
st.subheader("📝 Registro de Entrada de Pesos")

# Formulario para captura horizontal
with st.form(key=f"form_pesos_{st.session_state['form_key']}"):
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        maquina_input = st.selectbox("1. Máquina / Proceso", list(PRODUCTOS_PROCESO.keys()))
        
    with col2:
        # Menú dinámico según la máquina seleccionada
        materiales_opciones = PRODUCTOS_PROCESO[maquina_input]
        material_input = st.selectbox("2. Tipo de Material", materiales_opciones)
        
    with col3:
        cantidad_input = st.number_input("3. Cantidad Unidades", min_value=1, step=1, value=1)
        
    with col4:
        peso_input = st.number_input("4. Peso Registrado (Kg)", min_value=0.0, step=5.0, value=0.0)
        
    with col5:
        tara_input = st.number_input("5. Tara Uñas (Kg)", min_value=0.0, step=1.0, value=50.0)
        
    btn_registrar = st.form_submit_button("📥 Registrar Peso", type="primary", use_container_width=True)

# Lógica de guardado y limpieza del formulario
if btn_registrar:
    if peso_input <= tara_input and peso_input > 0:
        st.error("⚠️ El peso registrado en el montacargas debe ser mayor a la tara de las uñas.")
    elif peso_input == 0:
        st.error("⚠️ Por favor ingrese el peso capturado en el montacargas.")
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
        
        # Incrementar clave de formulario para reiniciar todos los campos
        st.session_state["form_key"] += 1
        st.success(f"✅ Se registró: {cantidad_input}x {material_input} ({maquina_input}) | Peso Neto: {peso_neto:.2f} Kg")
        st.rerun()

# -----------------------------------------------------------------------------
# 3. TABLA ESTILO EXCEL CON FILTROS
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📋 Registro Continuo y Hoja de Datos")

if df_cargas.empty:
    st.info("No hay registros acumulados todavía. Completa el formulario horizontal de arriba para añadir datos.")
else:
    # Filtros estilo Excel
    st.markdown("##### 🔍 Filtros de Búsqueda")
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        filtro_maquina = st.multiselect(
            "Filtrar por Proceso / Máquina:", 
            options=df_cargas["Proceso / Máquina"].unique(),
            default=df_cargas["Proceso / Máquina"].unique()
        )
        
    with f_col2:
        filtro_material = st.multiselect(
            "Filtrar por Tipo de Material:", 
            options=df_cargas["Tipo de Material"].unique(),
            default=df_cargas["Tipo de Material"].unique()
        )
    
    # Aplicar filtros
    df_filtrado = df_cargas[
        (df_cargas["Proceso / Máquina"].isin(filtro_maquina)) &
        (df_cargas["Tipo de Material"].isin(filtro_material))
    ]
    
    # Mostrar tabla interactiva de datos
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Botón de exportación
    csv_datos = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Hoja de Datos en CSV / Excel",
        data=csv_datos,
        file_name=f"registro_biomasa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
