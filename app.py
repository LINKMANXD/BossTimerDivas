import streamlit as st
from datetime import datetime, timedelta
import json, os

# Llamada a set_page_config debe ser la primera salida de Streamlit
st.set_page_config(page_title="Deva Timer Compartido", layout="centered")

# Inyectar CSS para botones estilizados
st.markdown("""
<style>
.green-button > button {
    border: 2px solid green;
    border-radius: 5px;
    padding: 0.25em 0.75em;
}
.purple-button > button {
    border: 2px solid purple;
    border-radius: 5px;
    padding: 0.25em 0.75em;
}
</style>
""", unsafe_allow_html=True)

# Archivo para estado compartido
SHARED_FILE = "shared_timers.json"

def load_shared_state():
    """Carga el estado compartido desde un JSON.
       El estado es un diccionario con la clave "channels", que es una lista de canales.
       Cada canal es un diccionario con 'name' y 'timer' (almacenado como string ISO o None)."""
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
        data = {"channels": [{"name": f"Canal {i}", "timer": None} for i in range(1, 9)]}
        save_shared_state(data)
    return data

def save_shared_state(data):
    """Guarda el estado compartido en un JSON, convirtiendo datetime a string ISO."""
    data_to_save = {"channels": []}
    for ch in data["channels"]:
        timer_val = ch["timer"].isoformat() if ch["timer"] is not None and isinstance(ch["timer"], datetime) else None
        data_to_save["channels"].append({"name": ch["name"], "timer": timer_val})
    with open(SHARED_FILE, "w") as f:
        json.dump(data_to_save, f)

# Configuración de la app
st.title("Deva Timer Compartido")
st.markdown("""
Esta herramienta permite a tu grupo ver y agregar tiempos para buscar bosses.
Los cambios se comparten en tiempo real (se actualiza cada segundo).

**Instrucciones:**
- Modifica el nombre del canal escribiendo en el campo.
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

# Cargar el estado compartido
data = load_shared_state()
channels = data["channels"]

def format_time_delta(td):
    """Devuelve el tiempo restante en mm:ss.
       Si el tiempo se acabó, muestra '¡Listo!' en rojo."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return '<span style="color:red;">¡Listo!</span>'
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

# Mostrar cada canal (editable) y sus controles
for idx, ch in enumerate(channels):
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    # Campo de texto para editar el nombre del canal
    new_name = col1.text_input("Canal", value=ch["name"], key=f"channel_name_{idx}")
    if new_name != ch["name"]:
        ch["name"] = new_name
        save_shared_state(data)
    if ch["timer"] is None:
        with col2:
            # Botón "Deva" con contorno verde
            with st.container():
                st.markdown('<div class="green-button">', unsafe_allow_html=True)
                if st.button("Deva", key=f"deva_{idx}"):
                    ch["timer"] = datetime.now() + timedelta(minutes=5)
                    save_shared_state(data)
                st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            # Botón "Deva Mut" con contorno morado
            with st.container():
                st.markdown('<div class="purple-button">', unsafe_allow_html=True)
                if st.button("Deva Mut", key=f"deva_mut_{idx}"):
                    ch["timer"] = datetime.now() + timedelta(minutes=8)
                    save_shared_state(data)
                st.markdown("</div>", unsafe_allow_html=True)
        with col4:
            st.write("Sin timer")
    else:
        remaining = ch["timer"] - datetime.now()
        with col2:
            st.markdown(format_time_delta(remaining), unsafe_allow_html=True)
        with col3:
            if st.button("Reiniciar 5 min", key=f"reiniciar_{idx}"):
                ch["timer"] = datetime.now() + timedelta(minutes=5)
                save_shared_state(data)
        with col4:
            if st.button("Resetear", key=f"resetear_{idx}"):
                ch["timer"] = None
                save_shared_state(data)
    st.markdown("---")  # Línea separadora entre canales
