import streamlit as st
from datetime import datetime, timedelta
import json, os

# --- Funciones para el estado compartido ---
SHARED_FILE = "shared_timers.json"

def load_shared_state():
    """Carga el estado compartido desde un archivo JSON.
       Convierte las marcas de tiempo (si existen) de string a datetime."""
    if os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, "r") as f:
            data = json.load(f)
        # Convertir tiempos guardados (si no son None) a objetos datetime
        for canal, valor in data["channels"].items():
            if valor is not None:
                try:
                    data["channels"][canal] = datetime.fromisoformat(valor)
                except Exception:
                    data["channels"][canal] = None
    else:
        # Estado inicial: 8 canales sin timer
        data = {"channels": {f"Canal {i}": None for i in range(1, 9)}}
        save_shared_state(data)
    return data

def save_shared_state(data):
    """Guarda el estado compartido en un archivo JSON.
       Antes de guardar, convierte los objetos datetime a string ISO."""
    data_a_guardar = {"channels": {}}
    for canal, valor in data["channels"].items():
        if valor is not None and isinstance(valor, datetime):
            data_a_guardar["channels"][canal] = valor.isoformat()
        else:
            data_a_guardar["channels"][canal] = None
    with open(SHARED_FILE, "w") as f:
        json.dump(data_a_guardar, f)

# --- Configuración de la App ---
st.set_page_config(page_title="Deva Timer Compartido", layout="centered")
st.title("Deva Timer Compartido")
st.markdown("""
Esta herramienta permite a tu grupo ver y agregar tiempos para buscar bosses.
Los cambios se comparten en tiempo real (actualiza automáticamente cada segundo).

**Instrucciones:**
- **Iniciar 5 min:** establece un timer de 5 minutos para el canal.
- **Iniciar 8 min:** establece un timer de 8 minutos para el canal.
- **Reiniciar 5 min:** reinicia el timer a 5 minutos.
- **Resetear:** borra el timer del canal.
""")

# Intentar usar auto-refresh (cada 1 segundo)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, limit=10000, key="frescador")
except ImportError:
    st.warning("Para auto-refresh, instala 'streamlit-autorefresh' o actualiza manualmente la página.")

# Cargar estado compartido
data = load_shared_state()
channels = data["channels"]

def format_time_delta(td):
    """Devuelve el tiempo restante en formato mm:ss o '¡Listo!' si ya se acabó."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return "¡Listo!"
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

# Mostrar cada canal en la interfaz
for canal, end_time in channels.items():
    # Verificar si hay timer activo y si faltan menos de 30 segundos
    red_border = False
    if end_time is not None:
        remaining = end_time - datetime.now()
        if remaining.total_seconds() < 30:
            red_border = True

    # Abrir un bloque HTML para el contenedor con borde condicional
    if red_border:
        st.markdown("<div style='border: 2px solid red; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='border: 2px solid transparent; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)
    
    # Mostrar la interfaz del canal usando columnas
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    with col1:
        st.markdown(f"### {canal}")
    if end_time is None:
        with col2:
            if st.button(f"Iniciar 5 min ({canal})"):
                channels[canal] = datetime.now() + timedelta(minutes=5)
                save_shared_state(data)
        with col3:
            if st.button(f"Iniciar 8 min ({canal})"):
                channels[canal] = datetime.now() + timedelta(minutes=8)
                save_shared_state(data)
        with col4:
            st.write("Sin timer")
    else:
        remaining = end_time - datetime.now()
        with col2:
            st.write(format_time_delta(remaining))
        with col3:
            if st.button(f"Reiniciar 5 min ({canal})"):
                channels[canal] = datetime.now() + timedelta(minutes=5)
                save_shared_state(data)
        with col4:
            if st.button(f"Resetear ({canal})"):
                channels[canal] = None
                save_shared_state(data)
    
    # Cerrar el bloque HTML del contenedor
    st.markdown("</div>", unsafe_allow_html=True)

