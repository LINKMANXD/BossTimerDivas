import streamlit as st
from datetime import datetime, timedelta
import json, os

# La configuración de la página debe hacerse antes de cualquier salida
st.set_page_config(page_title="Deva Timer Compartido", layout="centered")

# Inyectar CSS para botones personalizados
st.markdown("""
<style>
.green-button button {
    background-color: white;
    border: 2px solid green !important;
    color: green !important;
    font-weight: bold;
    margin: 0;
}
.purple-button button {
    background-color: white;
    border: 2px solid purple !important;
    color: purple !important;
    font-weight: bold;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

# Archivo para estado compartido
SHARED_FILE = "shared_timers.json"

def load_shared_state():
    """Carga el estado compartido desde un JSON.
    El estado es un diccionario con la clave "channels", que es una lista de canales.
    Cada canal es un dict con 'number' (del 1 al 30) y 'timer' (almacenado como string ISO o None)."""
    if os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, "r") as f:
            data = json.load(f)
        # Convertir timer a datetime si existe
        for ch in data["channels"]:
            if ch["timer"] is not None:
                try:
                    ch["timer"] = datetime.fromisoformat(ch["timer"])
                except Exception:
                    ch["timer"] = None
    else:
        # Inicializar 8 canales con números 1 a 8 por defecto
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
    """Para el canal idx, devuelve la lista de números disponibles (1 a 30)
       que no están usados por otros canales, pero incluye el valor actual del canal."""
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
    """Devuelve el tiempo restante en formato mm:ss; si se agotó, muestra '¡Listo!' en rojo."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return '<span style="color:red;">¡Listo!</span>'
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

# Título e instrucciones
st.title("Deva Timer Compartido")
st.markdown("""
Esta herramienta permite a tu grupo ver y agregar tiempos para buscar bosses.
Los cambios se comparten en tiempo real (se actualiza cada segundo).

**Instrucciones:**
- Selecciona el número de canal (del 1 al 30). Cada canal debe ser único.
- **Deva:** Establece un timer de 5 minutos (Deva normal).
- **Deva Mut:** Establece un timer de 8 minutos (Deva Mutante).
- **Reiniciar 5 min:** Reinicia el timer a 5 minutos.
- **Resetear:** Borra el timer del canal.
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
    # Usamos tres columnas:
    # col1: selección del número de canal
    # col2: botones "Deva" y "Deva Mut" (en línea, sin espacios)
    # col3: muestra el tiempo (en grande)
    col1, col2, col3 = st.columns([2, 3, 2])
    
    # Columna 1: Menú desplegable para elegir número de canal sin repeticiones
    options = get_available_options(idx, channels)
    current_val = ch.get("number", options[0])
    # Calcular el índice por defecto en las opciones
    try:
        default_index = options.index(current_val)
    except ValueError:
        default_index = 0
    selected = col1.selectbox("Canal", options, index=default_index, key=f"channel_select_{idx}")
    if selected != ch.get("number", None):
        ch["number"] = selected
        save_shared_state(data)
    
    # Columna 2: Botones "Deva" y "Deva Mut" juntos sin espacios
    deva_col, deva_mut_col = col2.columns(2)
    with deva_col:
        st.markdown('<div class="green-button">', unsafe_allow_html=True)
        if st.button("Deva", key=f"deva_{idx}"):
            ch["timer"] = datetime.now() + timedelta(minutes=5)
            save_shared_state(data)
        st.markdown("</div>", unsafe_allow_html=True)
    with deva_mut_col:
        st.markdown('<div class="purple-button">', unsafe_allow_html=True)
        if st.button("Deva Mut", key=f"deva_mut_{idx}"):
            ch["timer"] = datetime.now() + timedelta(minutes=8)
            save_shared_state(data)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Columna 3: Mostrar el tiempo en grande (si hay timer) o "Sin timer"
    if ch["timer"] is None:
        col3.markdown("<span style='font-size:2em;'>Sin timer</span>", unsafe_allow_html=True)
    else:
        remaining = ch["timer"] - datetime.now()
        time_display = format_time_delta(remaining)
        col3.markdown(f"<span style='font-size:2em;'>{time_display}</span>", unsafe_allow_html=True)
    
    # Si hay timer activo, debajo mostrar botones para "Reiniciar 5 min" y "Resetear"
    if ch["timer"] is not None:
        reset_col1, reset_col2 = st.columns(2)
        if reset_col1.button("Reiniciar 5 min", key=f"reiniciar_{idx}"):
            ch["timer"] = datetime.now() + timedelta(minutes=5)
            save_shared_state(data)
        if reset_col2.button("Resetear", key=f"resetear_{idx}"):
            ch["timer"] = None
            save_shared_state(data)
    st.markdown("---")
