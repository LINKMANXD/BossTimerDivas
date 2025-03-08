import streamlit as st
from datetime import datetime, timedelta
import json, os

# Configuración de la página (siempre debe ir antes de cualquier salida)
st.set_page_config(page_title="Deva Timer Compartido", layout="centered")

# Inyección de CSS para personalizar botones y reducir márgenes, con media queries para móviles
st.markdown("""
<style>
.green-button button {
    background-color: white;
    border: 2px solid green !important;
    color: green !important;
    font-weight: bold;
    margin: 2px !important;
    padding: 0.25em 0.5em !important;
}
.purple-button button {
    background-color: white;
    border: 2px solid purple !important;
    color: purple !important;
    font-weight: bold;
    margin: 2px !important;
    padding: 0.25em 0.5em !important;
}
@media (max-width: 600px) {
    .green-button button, .purple-button button {
        width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Archivo para estado compartido
SHARED_FILE = "shared_timers.json"

def load_shared_state():
    if os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, "r") as f:
            data = json.load(f)
        for ch in data["channels"]:
            if ch["timer"] is not None:
                try:
                    ch["timer"] = datetime.fromisoformat(ch["timer"])
                except Exception:
                    ch["timer"] = None
    else:
        # Inicialmente, creamos un único canal vacío
        data = {"channels": [{"number": None, "timer": None, "mode": None}]}
        save_shared_state(data)
    return data

def save_shared_state(data):
    data_to_save = {"channels": []}
    for ch in data["channels"]:
        timer_val = ch["timer"].isoformat() if ch["timer"] is not None and isinstance(ch["timer"], datetime) else None
        data_to_save["channels"].append({"number": ch["number"], "timer": timer_val, "mode": ch.get("mode")})
    with open(SHARED_FILE, "w") as f:
        json.dump(data_to_save, f)

def get_available_options(idx, channels):
    """Devuelve la lista de números (1 a 30) que no están usados en otros canales.
       Si el canal actual no tiene número, se asigna el menor disponible."""
    used = set()
    current = channels[idx].get("number")
    for i, ch in enumerate(channels):
        if i != idx and ch.get("number") is not None:
            used.add(ch["number"])
    options = [num for num in range(1, 31) if num not in used]
    if current is not None and current not in options:
        options.append(current)
    if current is None and options:
        current = options[0]
        channels[idx]["number"] = current
        save_shared_state(data)
    options.sort()
    return options

def format_time_delta(td):
    """Devuelve el tiempo restante en formato mm:ss con fuente grande; si se agotó, muestra '¡Listo!' en rojo."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return '<span style="color:red; font-size:2em;">¡Listo!</span>'
    minutes, seconds = divmod(total_seconds, 60)
    return f"<span style='font-size:2em;'>{minutes:02d}:{seconds:02d}</span>"

# Título y descripción (instrucciones)
st.title("Deva Timer Compartido")
st.markdown("""
Esta herramienta permite a tu grupo ver y agregar tiempos para buscar bosses. Los cambios se comparten en tiempo real (se actualiza cada segundo). Cuando muera un boss solo marca el que mataste para mantener un registro del tiempo.
""")

# Auto-refresh cada 1 segundo
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, limit=10000, key="frescador")
except ImportError:
    st.warning("Para auto-refresh, instala 'streamlit-autorefresh' o actualiza manualmente la página.")

# Cargar el estado compartido y asegurarse de que haya sólo un canal vacío al final
data = load_shared_state()
channels = data["channels"]

used_channels = [ch for ch in channels if ch["timer"] is not None]
empty_channels = [ch for ch in channels if ch["timer"] is None]
if empty_channels:
    empty_channel = empty_channels[0]
else:
    empty_channel = {"number": None, "timer": None, "mode": None}
channels = used_channels + [empty_channel]
# Si el último canal ya está en uso, agregamos un nuevo canal vacío
if channels and channels[-1]["timer"] is not None:
    channels.append({"number": None, "timer": None, "mode": None})
data["channels"] = channels
save_shared_state(data)

# Mostrar cada canal (dinámico)
for idx, ch in enumerate(channels):
    # Si el canal está en modo "deva_spawn", le agregamos un borde verde
    container_style = "padding: 5px; margin-bottom: 5px;"
    if ch.get("mode") == "deva_spawn":
        container_style = "border: 2px solid green; padding: 5px; margin-bottom: 5px;"
    st.markdown(f"<div style='{container_style}'>", unsafe_allow_html=True)
    
    # Dividimos en dos columnas: izquierda para selector y botones, derecha para mostrar tiempo
    col_left, col_right = st.columns([3, 2])
    with col_left:
        # Menú desplegable para seleccionar el número de canal
        options = get_available_options(idx, channels)
        current_val = ch.get("number")
        try:
            default_index = options.index(current_val)
        except ValueError:
            default_index = 0
        selected = st.selectbox("Canal", options, index=default_index, key=f"channel_select_{idx}")
        if selected != ch.get("number"):
            ch["number"] = selected
            save_shared_state(data)
        
        # Fila de botones, justo debajo del selector, en el siguiente orden:
        # "Deva", "Deva Spawn", "Deva Mutante" y "Quitar"
        btn_cols = st.columns(4)
        with btn_cols[0]:
            if st.button("Deva", key=f"deva_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=5)
                ch["mode"] = "deva"
                save_shared_state(data)
        with btn_cols[1]:
            if st.button("Deva Spawn", key=f"deva_spawn_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=2)
                ch["mode"] = "deva_spawn"
                save_shared_state(data)
        with btn_cols[2]:
            if st.button("Deva Mutante", key=f"deva_mutante_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=8)
                ch["mode"] = "deva_mut"
                save_shared_state(data)
        with btn_cols[3]:
            if st.button("Quitar", key=f"quitar_{idx}"):
                if len(channels) > 1:
                    data["channels"].pop(idx)
                    save_shared_state(data)
                    st.experimental_rerun()
    with col_right:
        if ch["timer"] is None:
            st.markdown("<span style='font-size:2em;'>Sin timer</span>", unsafe_allow_html=True)
        else:
            remaining = ch["timer"] - datetime.now()
            st.markdown(format_time_delta(remaining), unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
