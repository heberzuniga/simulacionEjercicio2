import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulación M/M/1 - Comparación", layout="wide")

st.title("📊 Evaluación de Alternativas - Sistema M/M/1 (Nivel Profesional)")

st.markdown("""
Esta aplicación permite comparar dos configuraciones de servicio bajo el modelo M/M/1,
incluyendo métricas clave y visualización gráfica para análisis gerencial.
""")

# =========================
# INPUTS
# =========================
st.sidebar.header("⚙️ Parámetros del Sistema")

lambda_rate = st.sidebar.number_input("Tasa de llegada λ (pacientes/hora)", value=20.0)
mu_a = st.sidebar.number_input("Tasa de servicio Alternativa A", value=26.0)
mu_b = st.sidebar.number_input("Tasa de servicio Alternativa B", value=32.0)

# =========================
# FUNCIÓN M/M/1
# =========================
def calcular_mm1(lmbda, mu):
    if mu <= lmbda:
        return None
    
    rho = lmbda / mu
    Lq = (rho**2) / (1 - rho)
    L = rho / (1 - rho)
    Wq = Lq / lmbda
    W = L / lmbda

    return {
        "rho": rho,
        "Lq": Lq,
        "L": L,
        "Wq": Wq * 60,  # minutos
        "W": W * 60     # minutos
    }

res_a = calcular_mm1(lambda_rate, mu_a)
res_b = calcular_mm1(lambda_rate, mu_b)

# =========================
# RESULTADOS NUMÉRICOS
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔵 Alternativa A")
    if res_a:
        for k, v in res_a.items():
            st.metric(k, f"{v:.2f}")
    else:
        st.error("Sistema inestable")

with col2:
    st.subheader("🟢 Alternativa B")
    if res_b:
        for k, v in res_b.items():
            st.metric(k, f"{v:.2f}")
    else:
        st.error("Sistema inestable")

# =========================
# TABLA COMPARATIVA
# =========================
st.subheader("📋 Comparación Tabular")

if res_a and res_b:
    df = pd.DataFrame({
        "Indicador": ["ρ (utilización)", "Lq (cola)", "L (sistema)", "Wq (min)", "W (min)"],
        "Alternativa A": [res_a["rho"], res_a["Lq"], res_a["L"], res_a["Wq"], res_a["W"]],
        "Alternativa B": [res_b["rho"], res_b["Lq"], res_b["L"], res_b["Wq"], res_b["W"]],
    })

    st.dataframe(df)

# =========================
# GRÁFICO 1: COMPARACIÓN DE TIEMPOS
# =========================
st.subheader("📈 Gráfico 1: Comparación de Tiempos")

if res_a and res_b:
    fig, ax = plt.subplots()

    tiempos = ["Wq (cola)", "W (sistema)"]
    valores_a = [res_a["Wq"], res_a["W"]]
    valores_b = [res_b["Wq"], res_b["W"]]

    x = range(len(tiempos))

    ax.bar([i - 0.2 for i in x], valores_a, width=0.4)
    ax.bar([i + 0.2 for i in x], valores_b, width=0.4)

    ax.set_xticks(x)
    ax.set_xticklabels(tiempos)
    ax.set_ylabel("Minutos")
    ax.set_title("Comparación de tiempos de espera")

    st.pyplot(fig)

# =========================
# GRÁFICO 2: CONGESTIÓN DEL SISTEMA
# =========================
st.subheader("📊 Gráfico 2: Congestión del Sistema")

if res_a and res_b:
    fig2, ax2 = plt.subplots()

    indicadores = ["Lq (cola)", "L (sistema)"]
    valores_a = [res_a["Lq"], res_a["L"]]
    valores_b = [res_b["Lq"], res_b["L"]]

    x = range(len(indicadores))

    ax2.bar([i - 0.2 for i in x], valores_a, width=0.4)
    ax2.bar([i + 0.2 for i in x], valores_b, width=0.4)

    ax2.set_xticks(x)
    ax2.set_xticklabels(indicadores)
    ax2.set_ylabel("Cantidad de pacientes")
    ax2.set_title("Nivel de congestión")

    st.pyplot(fig2)

# =========================
# ANÁLISIS AUTOMÁTICO
# =========================
st.subheader("🧠 Interpretación Automática")

if res_a and res_b:
    mejora = ((res_a["Wq"] - res_b["Wq"]) / res_a["Wq"]) * 100

    st.success(f"Mejora en tiempo de espera: {mejora:.2f}%")

    if mejora > 50:
        st.markdown("""
        ### 🔥 Recomendación de Nivel Profesional
        
        ✔ La Alternativa B reduce significativamente la congestión  
        ✔ Disminuye el tiempo de espera en más del 50%  
        ✔ Mejora la experiencia del paciente  
        ✔ Reduce estrés operativo  

        👉 **DECISIÓN: IMPLEMENTAR ALTERNATIVA B**
        """)
    else:
        st.warning("La mejora no es significativa. Evaluar costos.")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("Desarrollado para Simulación de Sistemas - Nivel Grandes Ligas 🚀")