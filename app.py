import math
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="M/M/1 Enterprise Extremo", layout="wide")

st.title("📈 Simulación M/M/1 - Enterprise Extremo")
st.markdown(
    """
    Aplicación profesional para comparar dos alternativas de servicio en un sistema **M/M/1**,
    incorporando:
    - **gráficos dinámicos con Plotly**
    - **simulación Monte Carlo**
    - **sensibilidad λ vs μ con mapa de calor**
    - **curvas de espera y utilización**
    """
)

# -----------------------------
# Funciones analíticas
# -----------------------------
def mm1_metrics(lmbda: float, mu: float):
    if lmbda <= 0 or mu <= 0:
        return None
    if mu <= lmbda:
        return None

    rho = lmbda / mu
    p0 = 1 - rho
    lq = rho**2 / (1 - rho)
    l_ = rho / (1 - rho)
    wq_hours = lq / lmbda
    w_hours = l_ / lmbda

    return {
        "rho": rho,
        "p0": p0,
        "Lq": lq,
        "L": l_,
        "Wq_h": wq_hours,
        "W_h": w_hours,
        "Wq_min": wq_hours * 60,
        "W_min": w_hours * 60,
    }

# -----------------------------
# Monte Carlo M/M/1
# -----------------------------
def simulate_mm1(lmbda: float, mu: float, n_customers: int = 10000, seed: int = 42):
    if mu <= lmbda or lmbda <= 0 or mu <= 0:
        return None

    rng = np.random.default_rng(seed)
    interarrivals = rng.exponential(1 / lmbda, n_customers)
    services = rng.exponential(1 / mu, n_customers)

    arrivals = np.cumsum(interarrivals)
    service_start = np.zeros(n_customers)
    departures = np.zeros(n_customers)
    waiting = np.zeros(n_customers)
    system_time = np.zeros(n_customers)
    queue_length_at_arrival = np.zeros(n_customers, dtype=int)

    service_start[0] = arrivals[0]
    departures[0] = service_start[0] + services[0]
    waiting[0] = 0
    system_time[0] = services[0]

    for i in range(1, n_customers):
        service_start[i] = max(arrivals[i], departures[i - 1])
        departures[i] = service_start[i] + services[i]
        waiting[i] = service_start[i] - arrivals[i]
        system_time[i] = departures[i] - arrivals[i]

        # clientes aún en el sistema al momento de llegada i
        queue_length_at_arrival[i] = np.sum(departures[:i] > arrivals[i])

    total_time = departures[-1] - arrivals[0]
    avg_num_system = np.sum(system_time) / total_time
    avg_num_queue = np.sum(waiting) / total_time

    return {
        "Wq_min": float(np.mean(waiting) * 60),
        "W_min": float(np.mean(system_time) * 60),
        "Lq": float(avg_num_queue),
        "L": float(avg_num_system),
        "rho_est": float(np.mean(services) / np.mean(system_time)) if np.mean(system_time) > 0 else np.nan,
        "arrivals": arrivals,
        "departures": departures,
        "waiting_series_min": waiting[: min(300, n_customers)] * 60,
        "system_series_min": system_time[: min(300, n_customers)] * 60,
        "queue_series": queue_length_at_arrival[: min(300, n_customers)],
    }


def recommendation_text(a, b):
    if not a or not b:
        return "No se puede recomendar porque al menos una alternativa es inestable."
    improvement = ((a["Wq_min"] - b["Wq_min"]) / a["Wq_min"]) * 100
    if improvement > 50:
        return (
            f"La **Alternativa B** domina claramente a la A. Reduce el tiempo de espera en cola en "
            f"**{improvement:.2f}%**, disminuye la congestión y entrega más holgura operativa."
        )
    if improvement > 20:
        return (
            f"La **Alternativa B** sigue siendo superior. La mejora en espera es de **{improvement:.2f}%** y "
            "es técnicamente recomendable si el costo adicional está justificado."
        )
    return "La mejora no es suficientemente agresiva; conviene complementar con análisis costo-beneficio."


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("⚙️ Parámetros del modelo")
lambda_rate = st.sidebar.number_input("Tasa de llegada λ (pacientes/hora)", min_value=0.01, value=20.0, step=1.0)
mu_a = st.sidebar.number_input("Tasa de servicio μ - Alternativa A", min_value=0.01, value=26.0, step=1.0)
mu_b = st.sidebar.number_input("Tasa de servicio μ - Alternativa B", min_value=0.01, value=32.0, step=1.0)

st.sidebar.header("🎲 Monte Carlo")
n_customers = st.sidebar.slider("Clientes simulados", min_value=1000, max_value=50000, value=10000, step=1000)
seed = st.sidebar.number_input("Semilla", min_value=0, value=42, step=1)

# -----------------------------
# Cálculo base
# -----------------------------
res_a = mm1_metrics(lambda_rate, mu_a)
res_b = mm1_metrics(lambda_rate, mu_b)
mc_a = simulate_mm1(lambda_rate, mu_a, n_customers=n_customers, seed=int(seed)) if res_a else None
mc_b = simulate_mm1(lambda_rate, mu_b, n_customers=n_customers, seed=int(seed) + 1) if res_b else None

# -----------------------------
# KPIs analíticos
# -----------------------------
st.subheader("📊 Indicadores analíticos M/M/1")
col1, col2 = st.columns(2)


def render_metrics(col, title, res):
    with col:
        st.markdown(f"### {title}")
        if not res:
            st.error("Sistema inestable: μ debe ser mayor que λ.")
            return
        m1, m2, m3 = st.columns(3)
        m1.metric("ρ Utilización", f"{res['rho']:.4f}")
        m2.metric("Wq (min)", f"{res['Wq_min']:.2f}")
        m3.metric("W (min)", f"{res['W_min']:.2f}")
        m4, m5, m6 = st.columns(3)
        m4.metric("Lq", f"{res['Lq']:.2f}")
        m5.metric("L", f"{res['L']:.2f}")
        m6.metric("P0", f"{res['p0']:.4f}")


render_metrics(col1, "🔵 Alternativa A", res_a)
render_metrics(col2, "🟢 Alternativa B", res_b)

if res_a and res_b:
    improvement = ((res_a["Wq_min"] - res_b["Wq_min"]) / res_a["Wq_min"]) * 100
    st.success(f"Mejora analítica de B frente a A en Wq: {improvement:.2f}%")
    st.info(recommendation_text(res_a, res_b))

# -----------------------------
# Tabla comparativa
# -----------------------------
if res_a and res_b:
    st.subheader("📋 Comparación analítica")
    df_compare = pd.DataFrame(
        {
            "Indicador": ["ρ", "P0", "Lq", "L", "Wq (min)", "W (min)"],
            "Alternativa A": [res_a["rho"], res_a["p0"], res_a["Lq"], res_a["L"], res_a["Wq_min"], res_a["W_min"]],
            "Alternativa B": [res_b["rho"], res_b["p0"], res_b["Lq"], res_b["L"], res_b["Wq_min"], res_b["W_min"]],
        }
    )
    st.dataframe(df_compare, use_container_width=True)

# -----------------------------
# Plotly dinámico: barras comparativas
# -----------------------------
if res_a and res_b:
    st.subheader("📈 Gráficos dinámicos con Plotly")
    chart_df = pd.DataFrame(
        {
            "Indicador": ["Wq (min)", "W (min)", "Lq", "L", "ρ"],
            "Alternativa A": [res_a["Wq_min"], res_a["W_min"], res_a["Lq"], res_a["L"], res_a["rho"]],
            "Alternativa B": [res_b["Wq_min"], res_b["W_min"], res_b["Lq"], res_b["L"], res_b["rho"]],
        }
    )
    chart_long = chart_df.melt(id_vars="Indicador", var_name="Alternativa", value_name="Valor")
    fig_bar = px.bar(chart_long, x="Indicador", y="Valor", color="Alternativa", barmode="group", title="Comparación dinámica de indicadores")
    st.plotly_chart(fig_bar, use_container_width=True)

    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(r=chart_df["Alternativa A"], theta=chart_df["Indicador"], fill='toself', name='Alternativa A'))
    radar_fig.add_trace(go.Scatterpolar(r=chart_df["Alternativa B"], theta=chart_df["Indicador"], fill='toself', name='Alternativa B'))
    radar_fig.update_layout(title="Radar comparativo", polar=dict(radialaxis=dict(visible=True)))
    st.plotly_chart(radar_fig, use_container_width=True)

# -----------------------------
# Monte Carlo
# -----------------------------
st.subheader("🎲 Simulación Monte Carlo")
mc_col1, mc_col2 = st.columns(2)


def render_mc(col, title, mc, analytic):
    with col:
        st.markdown(f"### {title}")
        if not mc or not analytic:
            st.error("No se simula porque el sistema es inestable.")
            return
        mc_table = pd.DataFrame(
            {
                "Métrica": ["Wq (min)", "W (min)", "Lq", "L"],
                "Analítico": [analytic["Wq_min"], analytic["W_min"], analytic["Lq"], analytic["L"]],
                "Monte Carlo": [mc["Wq_min"], mc["W_min"], mc["Lq"], mc["L"]],
            }
        )
        mc_table["Diferencia %"] = ((mc_table["Monte Carlo"] - mc_table["Analítico"]) / mc_table["Analítico"]) * 100
        st.dataframe(mc_table, use_container_width=True)

        sample_df = pd.DataFrame({
            "Cliente": np.arange(1, len(mc["waiting_series_min"]) + 1),
            "Espera en cola (min)": mc["waiting_series_min"],
            "Tiempo en sistema (min)": mc["system_series_min"],
        })
        fig_line = px.line(sample_df, x="Cliente", y=["Espera en cola (min)", "Tiempo en sistema (min)"], title="Trayectoria muestral de la simulación")
        st.plotly_chart(fig_line, use_container_width=True)


render_mc(mc_col1, "🔵 Monte Carlo - Alternativa A", mc_a, res_a)
render_mc(mc_col2, "🟢 Monte Carlo - Alternativa B", mc_b, res_b)

# -----------------------------
# Sensibilidad lambda vs mu
# -----------------------------
st.subheader("🧠 Sensibilidad λ vs μ (Heatmap)")
heat_col1, heat_col2 = st.columns(2)


def build_heatmap(mu_reference: float, title: str):
    lambdas = np.linspace(max(1, lambda_rate * 0.5), lambda_rate * 1.4, 30)
    mus = np.linspace(max(lambda_rate * 0.8, 1), mu_reference * 1.5, 30)
    z = np.full((len(mus), len(lambdas)), np.nan)

    for i, mu_val in enumerate(mus):
        for j, lam_val in enumerate(lambdas):
            metrics = mm1_metrics(lam_val, mu_val)
            if metrics:
                z[i, j] = metrics["Wq_min"]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=np.round(lambdas, 2),
        y=np.round(mus, 2),
        colorbar_title="Wq (min)",
        hovertemplate="λ=%{x}<br>μ=%{y}<br>Wq=%{z:.2f} min<extra></extra>"
    ))
    fig.add_vline(x=lambda_rate, line_dash="dash")
    fig.add_hline(y=mu_reference, line_dash="dash")
    fig.update_layout(title=title, xaxis_title="λ", yaxis_title="μ")
    return fig

with heat_col1:
    if res_a:
        st.plotly_chart(build_heatmap(mu_a, "Mapa de calor de Wq - Alternativa A"), use_container_width=True)
with heat_col2:
    if res_b:
        st.plotly_chart(build_heatmap(mu_b, "Mapa de calor de Wq - Alternativa B"), use_container_width=True)

# -----------------------------
# Curvas de sensibilidad
# -----------------------------
st.subheader("📉 Sensibilidad de espera al variar λ")
if res_a and res_b:
    lambda_series = np.linspace(1, min(mu_a, mu_b) - 0.1, 120)
    sens_df = pd.DataFrame({"λ": lambda_series})
    sens_df["Wq A (min)"] = [mm1_metrics(l, mu_a)["Wq_min"] if mm1_metrics(l, mu_a) else np.nan for l in lambda_series]
    sens_df["Wq B (min)"] = [mm1_metrics(l, mu_b)["Wq_min"] if mm1_metrics(l, mu_b) else np.nan for l in lambda_series]
    fig_sens = px.line(sens_df, x="λ", y=["Wq A (min)", "Wq B (min)"], title="Crecimiento no lineal de la espera cuando λ se acerca a μ")
    fig_sens.add_vline(x=lambda_rate, line_dash="dash")
    st.plotly_chart(fig_sens, use_container_width=True)

# -----------------------------
# Cierre ejecutivo
# -----------------------------
st.markdown("---")
st.markdown(
    "**Conclusión ejecutiva:** en teoría de colas, pequeñas mejoras en μ pueden provocar reducciones fuertes en Wq cuando el sistema opera cerca de saturación. "
    "Esta app permite demostrarlo analítica y computacionalmente."
)
