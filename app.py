import streamlit as st
from datetime import datetime, timedelta
import json, os
from filelock import FileLock

# --- Configuración de la página y CSS global ---
st.set_page_config(page_title="Deva Timer Compartido By LINKMANXD", layout="centered")
st.markdown("""
<style>
/* Fondo oscuro para toda la página */
body {
    background-color: #222;
    color: white;
    margin-top: 0px;
}

/* Reducir margen superior de los títulos */
h1 {
    margin-top: 5px;
}

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
.lightyellow-button button {
    background-color: white;
    border: 2px solid #FFFF99 !important;
    color: #B59B00 !important;
    font-weight: bold;
    margin: 2px !important;
    padding: 0.25em 0.5em !important;
}

/* Asegurar que los botones ocupen todo el ancho en móviles */
@media (max-width: 600px) {
    .green-button button, .purple-button button, .lightyellow-button button {
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

# --- Variables y funciones para persistencia ---
SHARED_FILE = "shared_timers.json"
LOCK_FILE = SHARED_FILE + ".lock"

def load_shared_state():
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
                data = {"channels": [{"number": None, "timer": None, "mode": None, "last_interaction": None}]}
                save_shared_state(data)
        else:
            data = {"channels": [{"number": None, "timer": None, "mode": None, "last_interaction": None}]}
            save_shared_state(data)
    for ch in data["channels"]:
        if ch["timer"] is not None:
            try:
                ch["timer"] = datetime.fromisoformat(ch["timer"])
            except Exception:
                ch["timer"] = None
        if ch.get("last_interaction") is not None:
            try:
                ch["last_interaction"] = datetime.fromisoformat(ch["last_interaction"])
            except Exception:
                ch["last_interaction"] = None
    return data

def save_shared_state(data):
    data_to_save = {"channels": []}
    for ch in data["channels"]:
        timer_val = ch["timer"].isoformat() if ch["timer"] is not None and isinstance(ch["timer"], datetime) else None
        li_val = ch["last_interaction"].isoformat() if ch.get("last_interaction") is not None and isinstance(ch["last_interaction"], datetime) else None
        data_to_save["channels"].append({
            "number": ch["number"],
            "timer": timer_val,
            "mode": ch.get("mode"),
            "last_interaction": li_val
        })
    lock = FileLock(LOCK_FILE)
    with lock:
        with open(SHARED_FILE, "w") as f:
            json.dump(data_to_save, f)

def get_available_options(idx, channels):
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
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return '<span style="color:red; font-size:2em;">¡Listo!</span>'
    minutes, seconds = divmod(total_seconds, 60)
    return f"<span style='color:{color}; font-size:2em;'>{minutes:02d}:{seconds:02d}</span>"

def clean_expired_channels(data):
    """Elimina canales cuyo temporizador llegó a cero y han pasado 40 segundos sin interacción
       (después de la expiración). Se toma como referencia la hora de expiración o la última interacción
       registrada posterior a la expiración."""
    now = datetime.now()
    nuevos = []
    for ch in data["channels"]:
        if ch["timer"] is not None and now > ch["timer"]:
            ref_time = ch["timer"]
            if ch.get("last_interaction") is not None and ch["last_interaction"] > ch["timer"]:
                ref_time = ch["last_interaction"]
            if (now - ref_time) > timedelta(seconds=40):
                continue
        nuevos.append(ch)
    if not any(ch["timer"] is None for ch in nuevos):
        nuevos.append({"number": None, "timer": None, "mode": None, "last_interaction": None})
    data["channels"] = nuevos
    save_shared_state(data)
    return data

def render_channel(ch, idx, channels, data):
    with st.container():
        st.markdown("<div class='channel-container'>", unsafe_allow_html=True)

        # Mostrar "Canal:" y el menú en la misma línea usando 2 columnas con gap="small"
        label_cols = st.columns([1, 4], gap="small")
        with label_cols[0]:
            st.markdown("**Canal:**", unsafe_allow_html=True)
        with label_cols[1]:
            options = get_available_options(idx, channels)
            current_val = ch.get("number")
            try:
                default_index = options.index(current_val)
            except ValueError:
                default_index = 0
            # Selectbox sin etiqueta, para que quede en la misma línea
            selected = st.selectbox("", options, index=default_index, key=f"channel_select_{idx}", label_visibility="collapsed")
            if selected != ch["number"]:
                ch["number"] = selected
                ch["last_interaction"] = datetime.now()
                save_shared_state(data)

        # Fila de botones: "Deva", "Deva Spawn", "Deva Mutant", "Quitar"
        btn_cols = st.columns(4)
        with btn_cols[0]:
            if st.button("Deva", key=f"deva_{idx}"):
                was_empty = (ch["timer"] is None)
                ch["timer"] = datetime.now() + timedelta(minutes=5)
                ch["mode"] = "deva"
                ch["last_interaction"] = datetime.now()
                save_shared_state(data)
                if was_empty and idx == len(channels) - 1:
                    st.experimental_rerun()
        with btn_cols[1]:
            if st.button("Deva Spawn", key=f"deva_spawn_{idx}"):
                was_empty = (ch["timer"] is None)
                ch["timer"] = datetime.now() + timedelta(minutes=2)
                ch["mode"] = "deva_spawn"
                ch["last_interaction"] = datetime.now()
                save_shared_state(data)
                if was_empty and idx == len(channels) - 1:
                    st.experimental_rerun()
        with btn_cols[2]:
            if st.button("Deva Mutant", key=f"deva_mutant_{idx}"):
                was_empty = (ch["timer"] is None)
                ch["timer"] = datetime.now() + timedelta(minutes=8)
                ch["mode"] = "deva_mut"
                ch["last_interaction"] = datetime.now()
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

# --- Título e instrucciones ---
st.title("Deva Timer Compartido By LINKMANXD")
st.markdown("""
Selecciona el canal y cuál boss es el que murió. Usa el botón Deva spawn para marcar la llegada del mutante en el canal.
""")

# --- Auto-refresh cada 1 segundo ---
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, limit=10000, key="frescador")
except ImportError:
    st.warning("Para auto-refresh, instala 'streamlit-autorefresh' o actualiza manualmente la página.")

# --- Cargar y limpiar estado compartido ---
data = load_shared_state()
data = clean_expired_channels(data)
channels = data["channels"]

# --- Ajuste dinámico de canales: mostrar usados y al menos un canal vacío ---
used_channels = [ch for ch in channels if ch["timer"] is not None]
empty_channels = [ch for ch in channels if ch["timer"] is None]
if empty_channels:
    empty_channel = empty_channels[0]
else:
    empty_channel = {"number": None, "timer": None, "mode": None, "last_interaction": None}
channels = used_channels + [empty_channel]
if channels and channels[-1]["timer"] is not None:
    channels.append({"number": None, "timer": None, "mode": None, "last_interaction": None})
data["channels"] = channels
save_shared_state(data)

# --- Renderizar canales en dos columnas para mayor compacidad ---
for i in range(0, len(channels), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        idx = i + j
        if idx < len(channels):
            with col:
                render_channel(channels[idx], idx, channels, data)
