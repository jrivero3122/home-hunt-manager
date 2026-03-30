import streamlit as st
import pandas as pd
import os
from datetime import datetime
import folium
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Home Hunt Manager | Pro", page_icon="🏠", layout="centered")

# --- 2. ESTILOS TAILWIND ---
st.markdown('<link href="https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("""
<style>
    .stApp { background-color: #f3f4f6; }
    .streamlit-expanderHeader {
        background-color: white; border-radius: 0px 0px 16px 16px !important;
        border: 1px solid #f3f4f6; border-top: none !important;
        color: #1a5276 !important; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS Y GPS ---
DB_AGENTES = "agentes.csv"
DB_VISITAS = "visitas.csv"

@st.cache_data(show_spinner=False, ttl=86400)
def geocode_address(address):
    try:
        geolocator = Nominatim(user_agent="galilei_realty_miami_pro")
        if "miami" not in address.lower() and "fl" not in address.lower():
            query = f"{address}, Miami, FL"
        else:
            query = address
        location = geolocator.geocode(query, timeout=5)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def cargar_datos(archivo, columnas):
    if not os.path.exists(archivo):
        return pd.DataFrame(columns=columnas)
    try:
        df = pd.read_csv(archivo)
        for col in columnas:
            if col not in df.columns: df[col] = ""
        if 'ID' in df.columns:
            df['ID'] = df['ID'].astype(str)
        return df
    except Exception:
        return pd.DataFrame(columns=columnas)

def guardar_datos(df, archivo):
    df.to_csv(archivo, index=False)

def limpiar(texto):
    return str(texto) if pd.notnull(texto) and str(texto).lower() != 'nan' else ""

COLS_AGENTES = ["ID", "Nombre", "Agencia", "Teléfono", "Email"]
COLS_VISITAS = ["ID", "Dirección", "Realtor_Nombre", "Realtor_Tel", "Fecha", "Hora", "Notas", "Visitada", "Lat", "Lng"]

IMG_PLACEHOLDER = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=150&q=80"

# --- 4. INTERFAZ ---
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<h1 class="text-4xl font-extrabold text-blue-900 m-0 p-0">Home Hunt Manager</h1>', unsafe_allow_html=True)
with col2:
    st.markdown('<p class="text-xs text-gray-400 mt-2">v.1.6 Pro Full</p>', unsafe_allow_html=True)

st.divider()

tabs = st.tabs(["📅 Visitas", "📍 Mapa", "➕ Nueva Cita", "👥 Agentes"])

# Extraer lista de agentes para los selectores de edición
df_agentes_global = cargar_datos(DB_AGENTES, COLS_AGENTES)
lista_nombres_global = df_agentes_global['Nombre'].tolist() if not df_agentes_global.empty else ["Sin Agentes"]

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    st.markdown('<h2 class="text-xl font-bold text-gray-700 mb-4">Mis Visitas Pendientes</h2>', unsafe_allow_html=True)
    df_visitas = cargar_datos(DB_VISITAS, COLS_VISITAS)
    
    if not df_visitas.empty:
        # ARREGLO DE ORDENAMIENTO: Limpieza y formato estricto
        df_visitas['Hora'] = df_visitas['Hora'].astype(str).str[:5] # Asegurar HH:MM
        df_visitas['dt'] = pd.to_datetime(df_visitas['Fecha'].astype(str) + ' ' + df_visitas['Hora'], errors='coerce')
        df_visitas = df_visitas.sort_values('dt', ascending=True) # Orden cronológico real
        
        visitas_mostradas = 0
        for i, row in df_visitas.iterrows():
            if str(row['Visitada']).strip() == "SÍ": continue
            visitas_mostradas += 1
            
            dir_v = limpiar(row['Dirección'])
            fecha_v = limpiar(row['Fecha'])
            realtor_n = limpiar(row['Realtor_Nombre'])
            realtor_t = ''.join(filter(str.isdigit, limpiar(row['Realtor_Tel'])))
            notas_v = limpiar(row['Notas'])
            
            # Formatear la hora para lectura humana (Ej: 02:30 PM)
            try:
                hora_obj = datetime.strptime(str(row['Hora']), "%H:%M")
                hora_v = hora_obj.strftime("%I:%M %p")
            except:
                hora_v = limpiar(row['Hora'])
            
            st.markdown(f"""
            <div class="flex items-center bg-white p-5 border border-gray-100 rounded-t-2xl shadow-lg mt-5">
                <img src="{IMG_PLACEHOLDER}" class="w-16 h-16 rounded-xl object-cover mr-5 shadow-inner">
                <div class="flex-grow">
                    <p class="font-bold text-gray-900 text-lg m-0 leading-tight">{dir_v}</p>
                    <p class="text-sm text-gray-500 m-0 mt-1 font-semibold text-blue-800">{fecha_v} a las {hora_v}</p>
                    <p class="text-xs text-gray-500 font-medium m-0 mt-1 uppercase">Realtor: {realtor_n}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("⬇️ Detalles, Notas y Edición", expanded=False):
                # PESTAÑAS INTERNAS PARA ORGANIZAR LA EDICIÓN
                t_notas, t_editar = st.tabs(["📝 Acciones y Notas", "✏️ Editar Cita"])
                
                with t_notas:
                    nuevas_notas = st.text_area("Notas de la visita:", value=notas_v, key=f"edit_notas_{i}", height=100)
                    if st.button("💾 Guardar Notas", key=f"save_edit_{i}"):
                        df_visitas.at[i, 'Notas'] = nuevas_notas
                        guardar_datos(df_visitas.drop(columns=['dt'], errors='ignore'), DB_VISITAS)
                        st.success("¡Notas actualizadas!")
                        st.experimental_rerun()
                    
                    st.markdown(f"""
                    <div class="flex justify-between mt-5 mb-3 px-1">
                        <a href="tel:{realtor_t}" class="w-5/12 bg-blue-900 text-white font-bold py-3 rounded-xl text-center text-sm no-underline shadow-md hover:bg-blue-800">📞 Llamar</a>
                        <a href="https://wa.me/{realtor_t}" class="w-5/12 bg-green-500 text-white font-bold py-3 rounded-xl text-center text-sm no-underline shadow-md hover:bg-green-600">💬 WhatsApp</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.divider()
                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.button("✅ Completar Visita", key=f"dn_{i}"):
                        df_visitas.at[i, 'Visitada'] = "SÍ"
                        guardar_datos(df_visitas.drop(columns=['dt'], errors='ignore'), DB_VISITAS)
                        st.experimental_rerun()
                    if col_btn2.button("🗑️ Borrar", key=f"del_{i}"):
                        df_visitas = df_visitas.drop(i)
                        guardar_datos(df_visitas.drop(columns=['dt'], errors='ignore'), DB_VISITAS)
                        st.experimental_rerun()
                
                with t_editar:
                    st.markdown("<small class='text-gray-500 mb-2'>Modifica los datos de esta cita:</small>", unsafe_allow_html=True)
                    
                    # Preparar datos actuales para el formulario
                    e_dir = st.text_input("Dirección", value=dir_v, key=f"edir_{i}")
                    
                    try:
                        idx_realtor = lista_nombres_global.index(realtor_n)
                    except:
                        idx_realtor = 0
                        
                    e_realtor = st.selectbox("Realtor", lista_nombres_global, index=idx_realtor, key=f"ereal_{i}")
                    
                    ce1, ce2 = st.columns(2)
                    try: 
                        fecha_dt = datetime.strptime(str(row['Fecha']), "%Y-%m-%d").date()
                    except: 
                        fecha_dt = datetime.now().date()
                        
                    try: 
                        hora_dt = datetime.strptime(str(row['Hora'])[:5], "%H:%M").time()
                    except: 
                        hora_dt = datetime.now().time()
                        
                    e_fecha = ce1.date_input("Fecha", value=fecha_dt, key=f"efec_{i}")
                    e_hora = ce2.time_input("Hora", value=hora_dt, key=f"ehor_{i}")
                    
                    if st.button("💾 Actualizar Datos", key=f"save_all_{i}"):
                        df_visitas.at[i, 'Dirección'] = e_dir
                        df_visitas.at[i, 'Realtor_Nombre'] = e_realtor
                        df_visitas.at[i, 'Fecha'] = e_fecha.strftime("%Y-%m-%d")
                        df_visitas.at[i, 'Hora'] = e_hora.strftime("%H:%M")
                        
                        # Si cambió la dirección, recalcular el GPS
                        if e_dir != dir_v:
                            lat, lng = geocode_address(e_dir)
                            df_visitas.at[i, 'Lat'] = lat if lat else ""
                            df_visitas.at[i, 'Lng'] = lng if lng else ""
                        
                        # Actualizar teléfono del realtor por si cambió
                        tel_nuevo = df_agentes_global[df_agentes_global['Nombre'] == e_realtor]['Teléfono'].iloc[0] if not df_agentes_global.empty else ""
                        df_visitas.at[i, 'Realtor_Tel'] = tel_nuevo
                        
                        guardar_datos(df_visitas.drop(columns=['dt'], errors='ignore'), DB_VISITAS)
                        st.experimental_rerun()
        
        if visitas_mostradas == 0:
            st.info("No tienes visitas pendientes.")
    else:
        st.info("Tu agenda está vacía. Registra tu próxima visita.")

# --- TAB 2: MAPA DE RUTA ---
with tabs[1]:
    st.markdown('<h2 class="text-xl font-bold text-gray-700 mb-4">Ubicación de Propiedades</h2>', unsafe_allow_html=True)
    df_mapa = cargar_datos(DB_VISITAS, COLS_VISITAS)
    
    if not df_mapa.empty:
        df_mapa = df_mapa[df_mapa['Visitada'] != "SÍ"].copy()
        
        if not df_mapa.empty:
            df_mapa['Lat'] = pd.to_numeric(df_mapa['Lat'], errors='coerce')
            df_mapa['Lng'] = pd.to_numeric(df_mapa['Lng'], errors='coerce')

            latitudes_validas = df_mapa['Lat'].dropna()
            longitudes_validas = df_mapa['Lng'].dropna()

            if not latitudes_validas.empty and not longitudes_validas.empty:
                centro_lat = latitudes_validas.mean()
                centro_lng = longitudes_validas.mean()
            else:
                centro_lat, centro_lng = 25.7617, -80.1918 

            m = folium.Map(location=[centro_lat, centro_lng], zoom_start=11)

            for i, row in df_mapa.iterrows():
                if pd.isna(row['Lat']) or pd.isna(row['Lng']):
                    lat = 25.7617 + (i * 0.008) 
                    lng = -80.1918 + (i * 0.008)
                else:
                    lat = row['Lat']
                    lng = row['Lng']
                    
                folium.Marker(
                    [lat, lng],
                    popup=f"<b>{row['Dirección']}</b><br>Realtor: {row['Realtor_Nombre']}",
                    tooltip=row['Dirección'],
                    icon=folium.Icon(color='blue', icon='home')
                ).add_to(m)

            components.html(m._repr_html_(), height=500)
        else:
            st.info("No tienes visitas pendientes para mostrar en el mapa.")
    else:
        st.warning("Agrega visitas para verlas en el mapa.")

# --- TAB 3: AGENDAR ---
with tabs[2]:
    st.subheader("Programar Nueva Visita")
    
    if df_agentes_global.empty:
        st.warning("⚠️ Primero debes añadir al menos un Agente en la pestaña '👥 Agentes'.")
    else:
        with st.form("form_crear", clear_on_submit=True):
            direccion = st.text_input("📍 Dirección Exacta (Ej: 8906 SW 6th Ln)")
            agente_seleccionado = st.selectbox("👤 Realtor", lista_nombres_global)
            
            c1, c2 = st.columns(2)
            fecha = c1.date_input("Fecha", value=datetime.now())
            hora = c2.time_input("Hora")
            notas = st.text_area("📝 Notas o instrucciones")
            
            if st.form_submit_button("Agendar y Localizar"):
                if direccion:
                    datos_agente = df_agentes_global[df_agentes_global['Nombre'] == agente_seleccionado]
                    telefono_agente = datos_agente['Teléfono'].iloc[0] if not datos_agente.empty else ""
                    
                    with st.spinner("📍 Localizando propiedad con el satélite..."):
                        lat_geo, lng_geo = geocode_address(direccion)
                    
                    nueva = {
                        "ID": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "Dirección": direccion, 
                        "Realtor_Nombre": agente_seleccionado, 
                        "Realtor_Tel": telefono_agente,
                        "Fecha": str(fecha), 
                        "Hora": hora.strftime("%H:%M"), # Guardado seguro 24h
                        "Notas": notas,
                        "Visitada": "NO", 
                        "Lat": lat_geo if lat_geo else "", 
                        "Lng": lng_geo if lng_geo else ""
                    }
                    df_v = cargar_datos(DB_VISITAS, COLS_VISITAS)
                    df_v = pd.concat([df_v, pd.DataFrame([nueva])], ignore_index=True)
                    guardar_datos(df_v, DB_VISITAS)
                    st.experimental_rerun()
                else:
                    st.error("La dirección es obligatoria.")

# --- TAB 4: AGENTES (AHORA TOTALMENTE EDITABLES) ---
with tabs[3]:
    st.header("Directorio de Agentes")
    
    with st.expander("➕ Añadir Nuevo Agente", expanded=False):
        with st.form("form_nuevo_agente", clear_on_submit=True):
            n_nombre = st.text_input("Nombre y Apellido *")
            n_agencia = st.text_input("Inmobiliaria / Agencia")
            n_tel = st.text_input("Teléfono *")
            n_email = st.text_input("Correo Electrónico")
            
            if st.form_submit_button("Guardar Agente"):
                if n_nombre and n_tel:
                    n_id = "AGT-" + datetime.now().strftime("%Y%m%d%H%M%S")
                    n_reg = {"ID": n_id, "Nombre": n_nombre, "Agencia": n_agencia, "Teléfono": n_tel, "Email": n_email}
                    
                    df_a = cargar_datos(DB_AGENTES, COLS_AGENTES)
                    df_a = pd.concat([df_a, pd.DataFrame([n_reg])], ignore_index=True)
                    guardar_datos(df_a, DB_AGENTES)
                    st.experimental_rerun()
                else:
                    st.error("Nombre y Teléfono son obligatorios.")

    st.divider()

    df_agentes_lista = cargar_datos(DB_AGENTES, COLS_AGENTES)
    
    if not df_agentes_lista.empty:
        for i, row in df_agentes_lista.iterrows():
            tel = limpiar(row['Teléfono'])
            email = limpiar(row['Email'])
            contacto_linea = f"{tel} • {email}" if email else tel
            
            st.markdown(f"""
            <div class="bg-white p-5 border-b border-gray-100 shadow-sm">
                <p class="text-xs text-blue-600 font-bold mb-1 tracking-wider uppercase">{contacto_linea}</p>
                <p class="text-xl text-gray-900 font-extrabold m-0 leading-tight">{limpiar(row['Nombre'])}</p>
                <p class="text-sm text-gray-500 m-0">{limpiar(row['Agencia'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # SECCIÓN DE EDICIÓN DE AGENTES
            with st.expander("⚙️ Gestión y Edición", expanded=False):
                st.markdown("<small class='text-gray-500 mb-2'>Modifica los datos del contacto:</small>", unsafe_allow_html=True)
                
                a_nom = st.text_input("Nombre", value=limpiar(row['Nombre']), key=f"an_{i}")
                a_age = st.text_input("Agencia", value=limpiar(row['Agencia']), key=f"aa_{i}")
                a_tel = st.text_input("Teléfono", value=limpiar(row['Teléfono']), key=f"at_{i}")
                a_eml = st.text_input("Email", value=limpiar(row['Email']), key=f"ae_{i}")
                
                ca1, ca2 = st.columns(2)
                if ca1.button("💾 Guardar Cambios", key=f"save_agt_{i}"):
                    df_agentes_lista.at[i, 'Nombre'] = a_nom
                    df_agentes_lista.at[i, 'Agencia'] = a_age
                    df_agentes_lista.at[i, 'Teléfono'] = a_tel
                    df_agentes_lista.at[i, 'Email'] = a_eml
                    guardar_datos(df_agentes_lista, DB_AGENTES)
                    
                    # También actualizamos el nombre del realtor en las visitas si lo cambió
                    if a_nom != limpiar(row['Nombre']):
                        df_v_update = cargar_datos(DB_VISITAS, COLS_VISITAS)
                        df_v_update.loc[df_v_update['Realtor_Nombre'] == limpiar(row['Nombre']), 'Realtor_Nombre'] = a_nom
                        guardar_datos(df_v_update, DB_VISITAS)
                        
                    st.experimental_rerun()
                    
                if ca2.button("🗑️ Eliminar Agente", key=f"del_agt_{row['ID']}"):
                    df_agentes_lista = df_agentes_lista[df_agentes_lista['ID'] != row['ID']]
                    guardar_datos(df_agentes_lista, DB_AGENTES)
                    st.experimental_rerun()
    else:
        st.info("No tienes agentes guardados. Añade uno arriba.")