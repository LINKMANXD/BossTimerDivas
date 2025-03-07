import streamlit as st
from datetime import datetime, timedelta
import json, os

# Configuración de la página (debe ir antes de cualquier salida)
st.set_page_config(page_title="Deva Timer Compartido", layout="centered")

# Inyección de CSS para personalizar botones y reducir márgenes (incluye media queries para móviles)
st.markdown("""
<style>
/* Botones con borde y márgenes reducidos */
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
/* Para dispositivos móviles, asegurar que los botones ocupen todo el ancho del contenedor */
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
    """Carga el estado compartido desde un JSON.
    Cada canal es un dict con 'number' (del 1 al 30) y 'timer' (string ISO o None)."""
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
        data = {"channels": [{"number": i, "timer": None} for i in range(1, 9)]}
        save_shared_state(data)
    return data

def save_shared_state(data):
    """Guarda el estado compartido en un JSON, convirtiendo datetime a string ISO."""
    data_to_save = {"channels": []}
    for ch in data["channels"]:
        timer_val = ch["timer"].isoformat() if ch["timer"] is not None and isinstance(ch["timer"], datetime) else None
        data_to_save["channels"].append({"number": ch["number"], "timer": timer_val})
    with open(SHARED_FILE, "w") as f:
        json.dump(data_to_save, f)

def get_available_options(idx, channels):
    """Devuelve la lista de números disponibles (1 a 30) para el canal idx, sin repetir."""
    used = set()
    current = channels[idx].get("number", None)
    for i, ch in enumerate(channels):
        if i != idx and ch.get("number") is not None:
            used.add(ch["number"])
    options = [num for num in range(1, 31) if num not in used]
    if current is not None and current not in options:
        options.append(current)
    options.sort()
    return options

def format_time_delta(td):
    """Devuelve el tiempo en mm:ss; si se agotó, muestra '¡Listo!' en rojo."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return '<span style="color:red;">¡Listo!</span>'
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

# Encabezado con el nuevo texto descriptivo
st.title("Deva Timer Compartido")
st.markdown("""
Esta herramienta permite a tu grupo ver y agregar tiempos para buscar bosses. Los cambios se comparten en tiempo real (se actualiza cada segundo). Cuando muera un boss solo marca el que mataste para mantener un registro del tiempo. By LINKMANXD
""")

# Auto-refresh cada 1 segundo
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, limit=10000, key="frescador")
except ImportError:
    st.warning("Para auto-refresh, instala 'streamlit-autorefresh' o actualiza manualmente la página.")

# Cargar estado compartido
data = load_shared_state()
channels = data["channels"]

# Mostrar cada canal y sus controles
for idx, ch in enumerate(channels):
    # Usamos dos columnas: la izquierda para menú y botones, la derecha para el tiempo
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Menú desplegable para elegir el número de canal
        options = get_available_options(idx, channels)
        current_val = ch.get("number", options[0])
        try:
            default_index = options.index(current_val)
        except ValueError:
            default_index = 0
        selected = st.selectbox("Canal", options, index=default_index, key=f"channel_select_{idx}")
        if selected != ch.get("number", None):
            ch["number"] = selected
            save_shared_state(data)
        
        # Agrupar botones "Deva" y "Deva Mut" en una fila con poco espacio
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.markdown('<div class="green-button">', unsafe_allow_html=True)
            if st.button("Deva", key=f"deva_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=5)
                save_shared_state(data)
            st.markdown("</div>", unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="purple-button">', unsafe_allow_html=True)
            if st.button("Deva Mut", key=f"deva_mut_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=8)
                save_shared_state(data)
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col_right:
        # Mostrar el tiempo en grande o "Sin timer"
        if ch["timer"] is None:
            st.markdown("<span style='font-size:2em;'>Sin timer</span>", unsafe_allow_html=True)
        else:
            remaining = ch["timer"] - datetime.now()
            time_display = format_time_delta(remaining)
            st.markdown(f"<span style='font-size:2em;'>{time_display}</span>", unsafe_allow_html=True)
    
    # Si hay timer activo, mostrar en una fila los botones "Reiniciar 5 min" y "Resetear" sin espacios extras
    if ch["timer"] is not None:
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            if st.button("Reiniciar 5 min", key=f"reiniciar_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=5)
                save_shared_state(data)
        with rcol2:
            if st.button("Resetear", key=f"resetear_{idx}"):
                ch["timer"] = None
                save_shared_state(data)
    st.markdown("---")
