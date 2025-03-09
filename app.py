import streamlit as st
from datetime import datetime, timedelta
import json, os
from filelock import FileLock

# Configuración de la página (debe ir antes de cualquier salida)
st.set_page_config(page_title="Deva Timer Compartido", layout="centered")

# Inyectar CSS para botones y contenedores compactos (incluye media queries para móviles)
st.markdown("""
<style>
/* Botones personalizados con márgenes reducidos */
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
/* Ajuste para dispositivos móviles */
@media (max-width: 600px) {
    .green-button button, .purple-button button {
        width: 100% !important;
    }
}
/* Contenedor compacto para cada canal */
.channel-container {
    display: block;
    padding: 4px;
    margin: 2px;
    border: 1px solid #555;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# Archivo que almacenará el estado compartido
SHARED_FILE = "shared_timers.json"
LOCK_FILE = SHARED_FILE + ".lock"

def load_shared_state():
    """Carga el estado compartido de forma segura usando filelock.
       Si hay error de lectura o el archivo está vacío/corrupto, se reinicializa."""
    lock = FileLock(LOCK_FILE)
    with lock:
        if os.path.exists(SHARED_FILE):
            try:
                with open(SHARED_FILE, "r") as f:
                    content = f.read().strip()
                    if content == "":
                        raise ValueError("Archivo vacío")
                    data = json.loads(content)
            except (json.JSONDecodeError, ValueError) as e:
                st.error("Error al leer el estado compartido. Se reinicializará el estado.")
                data = {"channels": [{"number": None, "timer": None, "mode": None}]}
                save_shared_state(data)
        else:
            data = {"channels": [{"number": None, "timer": None, "mode": None}]}
            save_shared_state(data)
    # Convertir timer a datetime
    for ch in data["channels"]:
        if ch["timer"] is not None:
            try:
                ch["timer"] = datetime.fromisoformat(ch["timer"])
            except Exception:
                ch["timer"] = None
    return data

def save_shared_state(data):
    """Guarda el estado compartido de forma segura usando filelock."""
    data_to_save = {"channels": []}
    for ch in data["channels"]:
        timer_val = ch["timer"].isoformat() if ch["timer"] is not None and isinstance(ch["timer"], datetime) else None
        data_to_save["channels"].append({"number": ch["number"], "timer": timer_val, "mode": ch.get("mode")})
    lock = FileLock(LOCK_FILE)
    with lock:
        with open(SHARED_FILE, "w") as f:
            json.dump(data_to_save, f)

def get_available_options(idx, channels):
    """Devuelve la lista de números (1 a 30) disponibles para el canal idx, sin repetir."""
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

def format_time_delta(td, color="white"):
    """Devuelve el tiempo restante en formato mm:ss con fuente grande; si se agota, muestra '¡Listo!' en rojo."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return '<span style="color:red; font-size:2em;">¡Listo!</span>'
    minutes, seconds = divmod(total_seconds, 60)
    return f"<span style='color:{color}; font-size:2em;'>{minutes:02d}:{seconds:02d}</span>"

def render_channel(ch, idx, channels, data):
    """Renderiza una 'tarjeta' compacta para un canal."""
    with st.container():
        st.markdown(f"<div class='channel-container'>", unsafe_allow_html=True)
        
        # Selector de canal
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
        
        # Fila de botones en orden: Deva, Deva Spawn, Deva Mutante, Quitar
        btn_cols = st.columns(4)
        with btn_cols[0]:
            if st.button("Deva", key=f"deva_{idx}"):
                was_empty = (ch["timer"] is None)
                ch["timer"] = datetime.now() + timedelta(minutes=5)
                ch["mode"] = "deva"
                save_shared_state(data)
                if was_empty and idx == len(channels) - 1:
                    st.experimental_rerun()
        with btn_cols[1]:
            if st.button("Deva Spawn", key=f"deva_spawn_{idx}"):
                was_empty = (ch["timer"] is None)
                ch["timer"] = datetime.now() + timedelta(minutes=2)
                ch["mode"] = "deva_spawn"
                save_shared_state(data)
                if was_empty and idx == len(channels) - 1:
                    st.experimental_rerun()
        with btn_cols[2]:
            if st.button("Deva Mutante", key=f"deva_mutante_{idx}"):
                was_empty = (ch["timer"] is None)
                ch["timer"] = datetime.now() + timedelta(minutes=8)
                ch["mode"] = "deva_mut"
                save_shared_state(data)
                if was_empty and idx == len(channels) - 1:
                    st.experimental_rerun()
        with btn_cols[3]:
            if st.button("Quitar", key=f"quitar_{idx}"):
                if len(channels) > 1:
                    data["channels"].pop(idx)
                    save_shared_state(data)
                    st.experimental_rerun()
        
        # Mostrar el temporizador
        if ch["timer"] is None:
            st.markdown("<span style='font-size:2em;'>Sin timer</span>", unsafe_allow_html=True)
        else:
            remaining = ch["timer"] - datetime.now()
            if ch.get("mode") == "deva_spawn":
                st.markdown(format_time_delta(remaining, color="yellow"), unsafe_allow_html=True)
            else:
                st.markdown(format_time_delta(remaining, color="white"), unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Título y descripción
st.title("Deva Timer Compartido")
st.markdown("""
Esta herramienta permite a tu grupo ver y agregar tiempos para buscar bosses. Los cambios se comparten en tiempo real (se actualiza cada segundo). Cuando muera un boss solo marca el que mataste para mantener un registro del tiempo.
""")

# Auto-refresh cada 1 segundo para actualizar el conteo
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, limit=10000, key="frescador")
except ImportError:
    st.warning("Para auto-refresh, instala 'streamlit-autorefresh' o actualiza manualmente la página.")

# Cargar estado compartido
data = load_shared_state()
channels = data["channels"]

# Ajuste dinámico de la lista de canales:
# Se muestran todos los canales usados, y se garantiza que siempre exista al menos UN canal vacío.
used_channels = [ch for ch in channels if ch["timer"] is not None]
empty_channels = [ch for ch in channels if ch["timer"] is None]
if empty_channels:
    empty_channel = empty_channels[0]
else:
    empty_channel = {"number": None, "timer": None, "mode": None}
channels = used_channels + [empty_channel]
if channels and channels[-1]["timer"] is not None:
    channels.append({"number": None, "timer": None, "mode": None})
data["channels"] = channels
save_shared_state(data)

# Mostrar los canales en un layout en dos columnas para mayor compacidad
for i in range(0, len(channels), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        idx = i + j
        if idx < len(channels):
            with col:
                render_channel(channels[idx], idx, channels, data)
