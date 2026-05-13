import streamlit as st
import numpy as np
import pandas as pd
from fractions import Fraction


# Escala AHP (Saaty) discreta
ahp_scale = [
    1/9, 1/8, 1/7, 1/6, 1/5, 1/4, 1/3, 1/2,
    1,
    2, 3, 4, 5, 6, 7, 8, 9
]


# -----------------------------
# UI
# -----------------------------

st.title("📊 AHP - Analytic Hierarchy Process")

with st.sidebar:
    st.header("Nível 1 — Overall Objective")
    objective = st.text_input("Overall Objective", value="Inserir o objetivo")

    st.divider()
    st.header("Nível 2 — Critérios")
    n = st.number_input("Quantidade de critérios (Nível 2)", min_value=2, max_value=5, value=3, step=1)

    criteria = []
    for i in range(int(n)):
        criteria.append(st.text_input(f"Critério Nível 2", value=f"C{i+1}", key=f"crit2_{i}"))

    st.divider()
    st.header("Alternativas")
    n_alt = st.number_input("Quantidade de alternativas", min_value=2, max_value=7, value=3, step=1)
    alternatives = []
    for i in range(int(n_alt)):
        alternatives.append(st.text_input(f"Alternativa {i+1}", value=f"A{i+1}", key=f"alt_{i}"))


#TODO Permitir adição de sub-critérios para cada critério de Nível 2

# -------------------------------
# Entrada de dados
# -------------------------------

st.write("## Matriz de Comparação")

# Inicializa matriz
matrix = np.ones((n, n))

cols = st.columns(n)

for i in range(n):
    for j in range(n):

        # UI dos complementares na matriz triangular inferior

        # UI dos Inputs das comparações na matriz triangular superior
        if i < j:
            value = cols[j].selectbox(
                f"{criteria[i]} vs {criteria[j]}",
                options=ahp_scale,
                format_func=lambda x: str(Fraction(x).limit_denominator()),
                key=f"{i}-{j}"
            )
            matrix[i, j] = value
            matrix[j, i] = 1 / value


# TODO Inserir o resto da matriz em disabled 

# -------------------------------
# Funções AHP
# -------------------------------
def calculate_priority_vector(matrix):
    col_sum = matrix.sum(axis=0)
    norm_matrix = matrix / col_sum
    priority_vector = norm_matrix.mean(axis=1)
    return priority_vector

def calculate_lambda_max(matrix, priority_vector):
    weighted_sum = matrix @ priority_vector
    lambda_max = (weighted_sum / priority_vector).mean()
    return lambda_max

def calculate_consistency_ratio(matrix, priority_vector):
    n = matrix.shape[0]
    
    RI_dict = {
        1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
    }
    
    lambda_max = calculate_lambda_max(matrix, priority_vector)
    CI = (lambda_max - n) / (n - 1)
    RI = RI_dict.get(n, 1.49)
    
    CR = CI / RI if RI != 0 else 0
    
    return lambda_max, CI, CR

# -------------------------------
# Cálculo
# -------------------------------
if st.button("Calcular AHP"):

    priority_vector = calculate_priority_vector(matrix)
    lambda_max, CI, CR = calculate_consistency_ratio(matrix, priority_vector)

    # -------------------------------
    # Resultados
    # -------------------------------
    st.write("## ✅ Resultados")

    df = pd.DataFrame({
        "Critério": criteria,
        "Peso": priority_vector
    }).sort_values(by="Peso", ascending=False)

    st.dataframe(df, use_container_width=True)

    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("λ máximo", round(lambda_max, 4))
    col2.metric("CI", round(CI, 4))
    col3.metric("CR", round(CR, 4))

    # Consistência
    if CR <= 0.1:
        st.success("✅ Consistência aceitável (CR ≤ 0.1)")
    else:
        st.error("⚠️ Consistência alta! Revise os julgamentos.")

    # Gráfico
    st.bar_chart(df.set_index("Critério"))