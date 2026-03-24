import streamlit as st

st.set_page_config(page_title="Simulación M/M/1 - Comparación", layout="wide")

st.title("📊 Evaluación de Alternativas - Sistema M/M/1")

st.markdown("Comparación entre dos configuraciones de atención en una clínica.")

# INPUTS
lambda_rate = st.number_input("Tasa de llegada λ (pacientes/hora)", value=20.0)
mu_a = st.number_input("Tasa de servicio Alternativa A", value=26.0)
mu_b = st.number_input("Tasa de servicio Alternativa B", value=32.0)


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
        "Wq": Wq,
        "W": W
    }


col1, col2 = st.columns(2)

# ALTERNATIVA A
with col1:
    st.subheader("🔵 Alternativa A")
    res_a = calcular_mm1(lambda_rate, mu_a)

    if res_a:
        st.metric("Utilización (ρ)", f"{res_a['rho']:.4f}")
        st.metric("Lq (cola)", f"{res_a['Lq']:.2f}")
        st.metric("L (sistema)", f"{res_a['L']:.2f}")
        st.metric("Wq (min)", f"{res_a['Wq']*60:.2f}")
        st.metric("W (min)", f"{res_a['W']*60:.2f}")
    else:
        st.error("Sistema inestable (μ ≤ λ)")

# ALTERNATIVA B
with col2:
    st.subheader("🟢 Alternativa B")
    res_b = calcular_mm1(lambda_rate, mu_b)

    if res_b:
        st.metric("Utilización (ρ)", f"{res_b['rho']:.4f}")
        st.metric("Lq (cola)", f"{res_b['Lq']:.2f}")
        st.metric("L (sistema)", f"{res_b['L']:.2f}")
        st.metric("Wq (min)", f"{res_b['Wq']*60:.2f}")
        st.metric("W (min)", f"{res_b['W']*60:.2f}")
    else:
        st.error("Sistema inestable (μ ≤ λ)")


# COMPARACIÓN
st.subheader("📈 Comparación y Mejora")

if res_a and res_b:
    mejora = ((res_a["Wq"] - res_b["Wq"]) / res_a["Wq"]) * 100
    st.success(f"Mejora en tiempo de espera en cola: {mejora:.2f}%")

    st.markdown("### 🧠 Interpretación Ejecutiva")

    if mejora > 30:
        st.write("""
        La Alternativa B representa una mejora significativa en el sistema.

        ✔ Reduce drásticamente los tiempos de espera  
        ✔ Disminuye congestión  
        ✔ Mejora la experiencia del paciente  
        ✔ Reduce estrés operativo  

        👉 Recomendación: IMPLEMENTAR ALTERNATIVA B
        """)
    else:
        st.write("La mejora no es significativa. Evaluar costos antes de decidir.")