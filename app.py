import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURAZIONE CORE ---
st.set_page_config(page_title="NEXUS | Quantum IDS", layout="wide", initial_sidebar_state="expanded")

# Inizializzazione degli stati di sessione
if 'angle' not in st.session_state:
    st.session_state.angle = 0.0
if 'was_mitigated' not in st.session_state:
    st.session_state.was_mitigated = False

# --- STILI CSS ---
st.markdown("""
    <style>
    .main {background-color: #03050a;}
    h1, h2, h3 {color: #00ffea; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 1px;}
    .css-1d391kg {background-color: #070a14;}
    .metric-container {background-color: #070a14; padding: 20px; border-radius: 10px; border: 1px solid #00ffea; box-shadow: 0 0 20px rgba(0, 255, 234, 0.15);}
    .math-box {background-color: #0a0a0a; padding: 15px; border-left: 5px solid #ff0055; margin-bottom: 20px; font-family: sans-serif; border-radius: 4px;}
    .info-box {background-color: #0a192f; padding: 20px; border-left: 5px solid #00ffea; margin-bottom: 20px; border-radius: 4px; color: #ccd6f6;}
    .terminal {background-color: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 10px; border-radius: 5px; height: 150px; overflow-y: auto; border: 1px solid #333;}
    hr {border-color: #1a2a42;}
    </style>
""", unsafe_allow_html=True)

# --- MOTORE MATEMATICO MULTIVARIABILE ---
@st.cache_data
def generate_3d_topology(intensity, target_ip, attack_type, resolution=50, mitigation=False):
    x_ip = np.linspace(0, 100, resolution)  
    t_time = np.linspace(0, 100, resolution)
    X, T = np.meshgrid(x_ip, t_time)
    
    baseline_Z = 20 + 3 * np.sin(X/3) + 3 * np.cos(T/3) + np.random.normal(0, 0.5, X.shape)
    Z = baseline_Z.copy()
    
    anomaly_coords = None
    
    if mitigation:
        intensity = intensity * 0.15  # Smorzamento topologico
    
    if attack_type != "Traffico Sicuro (Continuo)":
        if attack_type == "DDoS (Salto di Heaviside)":
            attack_mask = (X >= target_ip - 5) & (X <= target_ip + 5) & (T >= 45) & (T <= 55)
            Z[attack_mask] += intensity
            anomaly_coords = (target_ip, 50, Z.max())
            
        elif attack_type == "Memory Leak (Polo Asintotico)":
            dist = np.sqrt((X - target_ip)**2 + (T - 50)**2)
            with np.errstate(divide='ignore'):
                spike = (intensity * 10) / (dist + 0.5)
            Z += spike
            anomaly_coords = (target_ip, 50, Z.max())
            
        elif attack_type == "Blackhole / Packet Loss (Pozzo)":
            drop_mask = (X >= target_ip - 4) & (X <= target_ip + 4) & (T >= 46) & (T <= 54)
            Z[drop_mask] = 0 if not mitigation else 15
            anomaly_coords = (target_ip, 50, Z.min())

    grad_T, grad_X = np.gradient(Z)
    gradient_magnitude = np.sqrt(grad_X**2 + grad_T**2)
    
    return x_ip, t_time, X, T, Z, gradient_magnitude, anomaly_coords

def generate_logs(attack_type, target_ip, gradient_max, mitigation):
    logs = []
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    logs.append({"Time": now, "Component": "IDS_KERNEL", "Event": "Scansione Topologica Completa", "Status": "OK"})
    
    if attack_type != "Traffico Sicuro (Continuo)":
        if mitigation:
            logs.append({"Time": now, "Component": "IPS_FIREWALL", "Event": f"Filtro di smorzamento attivo su {target_ip}.x", "Status": "RESOLVED"})
            logs.append({"Time": now, "Component": "MATH_ENGINE", "Event": f"Gradiente assorbito a {gradient_max:.2f}", "Status": "OK"})
        else:
            logs.append({"Time": now, "Component": "IDS_SENSOR", "Event": f"Rilevata Discontinuità: {attack_type}", "Status": "CRITICAL"})
            logs.append({"Time": now, "Component": "MATH_ENGINE", "Event": f"Derivata parziale critica: ||∇S|| = {gradient_max:.2f}", "Status": "CRITICAL"})
    return pd.DataFrame(logs)

def style_demo_axis(ax, title):
    fig = ax.figure
    fig.patch.set_facecolor("#03050a")
    ax.set_facecolor("#070a14")
    ax.set_title(title, color="#00ffea", fontfamily="monospace", fontsize=12, pad=10)
    ax.tick_params(colors="#ccd6f6", labelsize=8)
    ax.grid(True, color="#1a2a42", linewidth=0.7, alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color("#00ffea")
        spine.set_alpha(0.55)

def generate_demo_graphs(
    continuous_level=1.0,
    jump_level=3.0,
    essential_level=1.0,
    stable_ping_level=1.2,
    spike_level=200,
    unstable_level=45,
):
    rng = np.random.default_rng(42)
    figures = []

    x = np.linspace(-3, 3, 300)
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(x, continuous_level * x ** 2, color="#00ffea", linewidth=2.4)
    style_demo_axis(ax, "Continua")
    figures.append(("Continua", fig, f"Funzione regolare senza interruzioni: parabola con intensità {continuous_level:g}."))

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot([-3, 0], [1, 1], color="#00ffea", linewidth=2.4)
    ax.plot([0, 3], [jump_level, jump_level], color="#ff0055", linewidth=2.4)
    ax.scatter([0], [1], facecolors="#070a14", edgecolors="#00ffea", s=55, zorder=3)
    ax.scatter([0], [jump_level], color="#ff0055", s=55, zorder=3)
    ax.set_xlim(-3, 3)
    ax.set_ylim(0, jump_level + 1)
    style_demo_axis(ax, "Salto")
    figures.append(("Salto", fig, f"Discontinuità improvvisa: il valore passa da 1 a {jump_level:g}."))

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    x_left = np.linspace(-3, -0.12, 240)
    x_right = np.linspace(0.12, 3, 240)
    ax.plot(x_left, essential_level / x_left, color="#00ffea", linewidth=2.2)
    ax.plot(x_right, essential_level / x_right, color="#ff0055", linewidth=2.2)
    ax.axvline(0, color="#ffff00", linestyle="--", linewidth=1.4, alpha=0.9)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-8 * essential_level, 8 * essential_level)
    style_demo_axis(ax, "Essenziale")
    figures.append(("Essenziale", fig, f"Asintoto verticale: intensità del polo pari a {essential_level:g}."))

    t = np.arange(60)
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(t, 20 + rng.normal(0, stable_ping_level, size=t.size), color="#00ffea", linewidth=1.9)
    ax.set_ylim(0, 230)
    style_demo_axis(ax, "Ping stabile")
    figures.append(("Ping stabile", fig, f"Latenza regolare con oscillazioni di circa {stable_ping_level:g} ms."))

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    lag_spike = 20 + rng.normal(0, 1.4, size=t.size)
    lag_spike[32] = spike_level
    ax.plot(t, lag_spike, color="#00ffea", linewidth=1.9)
    ax.scatter([32], [spike_level], color="#ff0055", s=48, zorder=3)
    ax.set_ylim(0, spike_level + 30)
    style_demo_axis(ax, "Lag spike")
    figures.append(("Lag spike", fig, f"Connessione quasi stabile con un picco isolato fino a {spike_level} ms."))

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(t, np.clip(rng.normal(80, unstable_level, size=t.size), 5, 220), color="#ff0055", linewidth=1.9)
    ax.set_ylim(0, 230)
    style_demo_axis(ax, "Instabile")
    figures.append(("Instabile", fig, f"Latenza ad alta variabilità: deviazione impostata a {unstable_level} ms."))

    for _, fig, _ in figures:
        fig.tight_layout(pad=1.2)

    return figures

# --- NAVIGAZIONE ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/120px-Python-logo-notext.svg.png", width=40)
st.sidebar.title("NEXUS OS")
page = st.sidebar.radio("Moduli di Sistema", ["📡 Scanner IDS Live", "📐 Libreria Matematica", "📊 Demo grafici", "🛡️ Manuale Operativo Cyber"])
st.sidebar.divider()

# ==========================================
# PAGINA 1: SCANNER IDS LIVE
# ==========================================
if page == "📡 Scanner IDS Live":
    st.sidebar.subheader("Pannello di Controllo")
    auto_rotate = st.sidebar.toggle("🌀 Scansione Orbitale Automatica", value=False)
    
    attack_type = st.sidebar.selectbox("Vettore Matematico / Attacco:", 
                                   ["Traffico Sicuro (Continuo)", 
                                    "DDoS (Salto di Heaviside)", 
                                    "Memory Leak (Polo Asintotico)",
                                    "Blackhole / Packet Loss (Pozzo)"])
    
    intensity = st.sidebar.slider("Magnitudo Anomalia", 50, 300, 150, disabled=(attack_type=="Traffico Sicuro (Continuo)"))
    target_ip = st.sidebar.slider("Subnet Target", 10, 90, 50, disabled=(attack_type=="Traffico Sicuro (Continuo)"))

    st.sidebar.divider()
    st.sidebar.subheader("Sistemi di Difesa")
    mitigation_active = st.sidebar.toggle("🛡️ Attiva Contromisure IPS", value=False)

    # --- LOGICA DI TRANSIZIONE (MITIGAZIONE ANIMATA) ---
    if mitigation_active and not st.session_state.was_mitigated and attack_type != "Traffico Sicuro (Continuo)":
        # L'utente ha appena attivato la difesa: mostra l'animazione di transizione
        st.info("⚠️ Discontinuità rilevata. Inizializzazione protocolli di sicurezza...")
        prog_testo = st.empty()
        prog_bar = st.progress(0)
        
        for i in range(100):
            if i < 30:
                prog_testo.markdown(f"*> Calcolo matrice inversa in corso... {i}%*")
            elif i < 70:
                prog_testo.markdown(f"*> Applicazione filtro Gaussiano sulla subnet {target_ip}.x... {i}%*")
            else:
                prog_testo.markdown(f"*> Smorzamento topologico e ripristino continuità... {i}%*")
            
            prog_bar.progress(i + 1)
            time.sleep(0.02) # Velocità dell'animazione
            
        prog_testo.empty()
        prog_bar.empty()
        st.toast("Anomalia riassorbita. Rete stabile.", icon="✅")
        st.session_state.was_mitigated = True
        st.rerun() # Ricarica per mostrare il grafico guarito
        
    elif not mitigation_active and st.session_state.was_mitigated:
        # L'utente ha disattivato la difesa
        st.session_state.was_mitigated = False
        st.toast("Scudi disattivati. Rete vulnerabile.", icon="⚠️")

    # --- GENERAZIONE DATI E RENDER ---
    x_ip, t_time, X, T, Z, gradient, anomaly = generate_3d_topology(intensity, target_ip, attack_type, mitigation=mitigation_active)

    st.title("📡 Radar Topologico Live")
    st.markdown("Monitoraggio in tempo reale della varietà differenziabile della rete.")
    
    fig_3d = go.Figure()
    
    if attack_type == "Traffico Sicuro (Continuo)" or mitigation_active: colorscale = 'Teal'
    elif attack_type == "Blackhole / Packet Loss (Pozzo)": colorscale = 'Cividis'
    else: colorscale = 'Inferno'

    fig_3d.add_trace(go.Surface(
        z=Z, x=x_ip, y=t_time, surfacecolor=gradient, colorscale=colorscale, opacity=0.9,
        lighting=dict(roughness=0.5, ambient=0.4, diffuse=0.8, specular=0.5), 
        contours=dict(z=dict(show=True, usecolormap=True, highlightcolor="white", project_z=True), x=dict(show=False), y=dict(show=False))
    ))

    cam_z = 1.0 if attack_type != "Blackhole / Packet Loss (Pozzo)" else -0.8
    if auto_rotate:
        radius = 1.8
        camera_eye = dict(x=radius * np.cos(st.session_state.angle), y=radius * np.sin(st.session_state.angle), z=cam_z)
    elif anomaly:
        camera_eye = dict(x=1.5 * (target_ip/50 - 1), y=-1.8, z=cam_z)
    else:
        camera_eye = dict(x=1.2, y=-1.5, z=cam_z)

    if anomaly and not mitigation_active:
        fig_3d.add_trace(go.Scatter3d(
            x=[anomaly[0], anomaly[0]], y=[anomaly[1], anomaly[1]], z=[Z.max() + 15, 0],
            mode='lines+markers+text', line=dict(color='red', width=4, dash='dash'),
            marker=dict(size=[8, 0], color='yellow', symbol='diamond'),
            text=["🔥 LOCK ON", ""], textposition="top center", name="Target"
        ))
    elif anomaly and mitigation_active:
        fig_3d.add_trace(go.Scatter3d(
            x=[anomaly[0]], y=[anomaly[1]], z=[anomaly[2] + 5],
            mode='markers+text', marker=dict(size=5, color='cyan', symbol='circle'),
            text=["🛡️ MITIGATO"], textposition="top center", name="Secured"
        ))

    fig_3d.update_layout(
        template="plotly_dark",
        scene=dict(xaxis_title="Spazio (IP)", yaxis_title="Tempo (t)", zaxis_title="Volume", camera=dict(eye=camera_eye)),
        margin=dict(l=0, r=0, b=0, t=0), height=500
    )
    st.plotly_chart(fig_3d, use_container_width=True)

    col_logs, col_tools = st.columns([2, 1])
    with col_logs:
        st.subheader("Console Eventi SIEM")
        df_logs = generate_logs(attack_type, target_ip, gradient.max(), mitigation_active)
        
        def color_status(val):
            color = '#ff3333' if val == 'CRITICAL' else ('#00ffcc' if val == 'RESOLVED' else '#a0a0a0')
            return f'color: {color}; font-weight: bold;'
        
        st.dataframe(df_logs.style.map(color_status, subset=['Status']), use_container_width=True, hide_index=True)

    with col_tools:
        st.subheader("Strumenti Forensi")
        st.markdown("Estrazione tensore per Machine Learning.")
        
        df_export = pd.DataFrame({'IP_Subnet': X.flatten(), 'Time_ms': T.flatten(), 'Volume': Z.flatten(), 'Gradient': gradient.flatten()})
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(label="💾 Scarica Dati (CSV)", data=csv_data, file_name=f"nexus_log_{datetime.now().strftime('%H%M')}.csv", mime="text/csv", type="primary")
        
        if mitigation_active:
            st.success("✅ Rete messa in sicurezza.")
        elif attack_type != "Traffico Sicuro (Continuo)":
            st.error("⚠️ In attesa di mitigazione...")

    if auto_rotate:
        st.session_state.angle += 0.08
        if st.session_state.angle > 2 * np.pi: st.session_state.angle = 0.0
        time.sleep(0.04)
        st.rerun()

# ==========================================
# PAGINA 2: TEORIA MATEMATICA
# ==========================================
elif page == "📐 Libreria Matematica":
    st.title("📐 Topologia delle Discontinuità")
    st.markdown("Questa sezione illustra i concetti di Analisi Matematica alla base del motore di rilevamento.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="math-box"><h3>1. Discontinuità a Salto</h3>
        Il limite destro e sinistro esistono ma differiscono.</div>""", unsafe_allow_html=True)
        st.latex(r"\lim_{t \to t_0^-} f(t) \neq \lim_{t \to t_0^+} f(t)")
    with col2:
        st.markdown("""<div class="math-box"><h3>2. Discontinuità Essenziale</h3>
        Almeno uno dei due limiti tende a infinito.</div>""", unsafe_allow_html=True)
        st.latex(r"\lim_{t \to t_0} f(t) = \pm \infty")
    st.divider()
    st.markdown("""<div class="math-box"><h3>3. Discontinuità Eliminabile</h3>
    Il limite esiste ma la funzione non è definita nel punto.</div>""", unsafe_allow_html=True)
    st.latex(r"\lim_{t \to t_0} f(t) = L \quad \text{ma} \quad f(t_0) \neq L")

# ==========================================
# PAGINA 3: DEMO GRAFICI
# ==========================================
elif page == "📊 Demo grafici":
    st.title("📊 Demo grafici")
    st.markdown("Visualizzazione rapida di continuità, discontinuità e pattern di latenza.")

    slider_specs = [
        ("continuous_level", "Intensità continua", 0.5, 3.0, 1.0, 0.25),
        ("jump_level", "Ampiezza salto", 2.0, 8.0, 3.0, 0.5),
        ("essential_level", "Intensità asintoto", 0.5, 3.0, 1.0, 0.25),
        ("stable_ping_level", "Oscillazione ping stabile", 0.2, 5.0, 1.2, 0.2),
        ("spike_level", "Intensità lag spike", 60, 300, 200, 10),
        ("unstable_level", "Variabilità instabile", 10, 90, 45, 5),
    ]
    demo_levels = {}
    render_slots = []

    for row_start in range(0, len(slider_specs), 3):
        cols = st.columns(3)
        for col, slider_spec in zip(cols, slider_specs[row_start:row_start + 3]):
            key, label, min_value, max_value, default_value, step = slider_spec
            with col:
                demo_levels[key] = st.slider(label, min_value, max_value, default_value, step, key=key)
                render_slots.append((st.empty(), st.empty()))

    demo_figures = generate_demo_graphs(**demo_levels)
    for (plot_slot, caption_slot), (_, fig, caption) in zip(render_slots, demo_figures):
        plot_slot.pyplot(fig, width="stretch")
        caption_slot.caption(caption)
        plt.close(fig)

# ==========================================
# PAGINA 4: MANUALE OPERATIVO
# ==========================================
elif page == "🛡️ Manuale Operativo Cyber":
    st.title("🛡️ Mappatura Minacce")
    st.markdown("""
    <div class="info-box"><h2>💥 DDoS</h2><strong>Matematica:</strong> Discontinuità a Salto.<br>Salto innaturale nel volume dei dati.</div>
    <div class="info-box" style="border-left-color: #ff0055;"><h2>🔥 Memory Leak</h2><strong>Matematica:</strong> Polo Asintotico.<br>Le risorse consumate crescono verso l'infinito.</div>
    <div class="info-box" style="border-left-color: #ffff00;"><h2>🕳️ Blackhole Routing</h2><strong>Matematica:</strong> Discontinuità Eliminabile.<br>I pacchetti spariscono improvvisamente dal dominio.</div>
    """, unsafe_allow_html=True)
