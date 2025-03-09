import streamlit as st
from datetime import datetime, timedelta
import json, os

# Configuración de la página (debe ir antes de cualquier salida)
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
        try:
            with open(SHARED_FILE, "r") as f:
                content = f.read().strip()
                if content == "":
                    raise ValueError("Archivo vacío")
                data = json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            st.error("Error al leer el estado compartido. Se reiniciará el estado.")
            data = {"channels": [{"number": None, "timer": None, "mode": None}]}
            save_shared_state(data)
        for ch in data["channels"]:
            if ch["timer"] is not None:
                try:
                    ch["timer"] = datetime.fromisoformat(ch["timer"])
                except Exception:
                    ch["timer"] = None
    else:
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

data = load_shared_state()
channels = data["channels"]

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

for idx, ch in enumerate(channels):
    st.markdown("<div style='padding:5px; margin-bottom:5px;'>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([3, 2])
    with col_left:
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
    with col_right:
        if ch["timer"] is None:
            st.markdown("<span style='font-size:2em;'>Sin timer</span>", unsafe_allow_html=True)
        else:
            remaining = ch["timer"] - datetime.now()
            if ch.get("mode") == "deva_spawn":
                st.markdown(format_time_delta(remaining, color="yellow"), unsafe_allow_html=True)
            else:
                st.markdown(format_time_delta(remaining, color="white"), unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
