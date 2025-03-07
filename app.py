import streamlit as st
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Deva Timer", layout="centered")

st.title("Deva Timer")
st.markdown("""
Esta herramienta te ayudará a llevar un registro de los tiempos de aparición de los bosses en cada canal.
- **Deva normal:** Temporizador de 5 minutos.
- **Deva mutante:** Temporizador de 8 minutos.

### Instrucciones:
- Haz clic en "**Iniciar 5 min**" para un Deva normal.
- Haz clic en "**Iniciar 8 min**" para un Deva mutante.
- Usa "**Reiniciar 5 min**" para reiniciar un temporizador a 5 minutos.
- Usa "**Resetear**" para borrar el temporizador de un canal.
""")

# Inicializar el estado de los canales en session_state (8 canales)
if "channels" not in st.session_state:
    st.session_state.channels = {f"Canal {i}": None for i in range(1, 9)}

# Intentar usar auto-refresh cada 1 segundo (opcional)
try:
    from streamlit_autorefresh import st_autorefresh
    # Auto-refresh: actualiza cada 1000 ms (1 segundo), hasta 10,000 veces
    st_autorefresh(interval=1000, limit=10000, key="frescador")
except ImportError:
    st.warning("Para auto-refresh, instala el paquete 'streamlit-autorefresh' o refresca manualmente la página.")

def format_time_delta(td):
    """Convierte un timedelta en formato mm:ss o muestra '¡Listo!' si el tiempo se acabó."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return "¡Listo!"
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

# Mostrar la interfaz para cada canal
for canal, end_time in st.session_state.channels.items():
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    with col1:
        st.markdown(f"### {canal}")
    if end_time is None:
        with col2:
            if st.button(f"Iniciar 5 min ({canal})"):
                st.session_state.channels[canal] = datetime.now() + timedelta(minutes=5)
        with col3:
            if st.button(f"Iniciar 8 min ({canal})"):
                st.session_state.channels[canal] = datetime.now() + timedelta(minutes=8)
        with col4:
            st.write("Sin timer")
    else:
        remaining = end_time - datetime.now()
        with col2:
            st.write(format_time_delta(remaining))
        with col3:
            if st.button(f"Reiniciar 5 min ({canal})"):
                st.session_state.channels[canal] = datetime.now() + timedelta(minutes=5)
        with col4:
            if st.button(f"Resetear ({canal})"):
                st.session_state.channels[canal] = None
