import streamlit as st
import numpy as np
import pandas as pd
from fractions import Fraction
from services.ahp_calc import calcular_ahp


def show():

    # -----------------------------
    # UI
    # -----------------------------
    st.title("AHP - Analytic Hierarchy Process")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()

    # Escala AHP
    ahp_scale = [
        1,1/9, 1/8, 1/7, 1/6, 1/5, 1/4, 1/3, 1/2,
        2, 3, 4, 5, 6, 7, 8, 9
    ]

    with st.sidebar:
        st.header("Nível 1 — Overall Objective")
        objective = st.text_input("Overall Objective", value="Inserir o objetivo")

        st.divider()
        st.header("Nível 2 — Critérios")

        n = st.number_input(
            "Quantidade de critérios",
            min_value=2, max_value=5, value=3, step=1
        )

        criteria = [
            st.text_input(f"Critério {i+1}", value=f"C{i+1}", key=f"crit_{i}")
            for i in range(int(n))
        ]

    # -------------------------------
    # Matriz
    # -------------------------------
    st.write("## Matriz de Comparação")

    matrix = np.ones((n, n))

    header = st.columns(n + 1)
    header[0].markdown("**Critério**")
    for j in range(n):
        header[j + 1].markdown(f"**{criteria[j]}**")

    for i in range(n):
        row = st.columns(n + 1)
        row[0].markdown(f"**{criteria[i]}**")

        for j in range(n):

            if i == j:
                matrix[i, j] = 1
                row[j + 1].markdown("1")

            elif i < j:
                value = row[j + 1].selectbox(
                    "",
                    ahp_scale,
                    format_func=lambda x: str(Fraction(x).limit_denominator()),
                    key=f"{i}-{j}",
                    label_visibility="collapsed"
                )

                matrix[i, j] = value
                matrix[j, i] = 1 / value

            else:
                row[j + 1].markdown(
                    str(Fraction(matrix[i, j]).limit_denominator()),
                    unsafe_allow_html=True
                )

    # -------------------------------
    # Cálculo parâmetros AHp
    # -------------------------------
    result = calcular_ahp(matrix)

    # -------------------------------
    # Exibição
    # -------------------------------

    # Soma das colunas
    st.write("## Soma das Colunas")
    column_sums_df = pd.DataFrame(
        [result["column_sums"]],
        columns=criteria,
        index=["Soma"]
    )
    st.dataframe(column_sums_df.style.format("{:.4f}"), use_container_width=True)

    # Normalizada
    st.write("## Matriz Normalizada")
    normalized_df = pd.DataFrame(
        result["normalized_matrix"],
        index=criteria,
        columns=criteria
    )
    st.dataframe(normalized_df.style.format("{:.4f}"), use_container_width=True)

    # Pesos
    st.write("## Vetor de Prioridade")
    priority_df = pd.DataFrame({
        "Critério": criteria,
        "Peso": result["priority_vector"],
        "Peso (%)": result["priority_vector"] * 100
    })
    st.dataframe(
        priority_df.style.format({
            "Peso": "{:.4f}",
            "Peso (%)": "{:.2f}%"
        }),
        use_container_width=True
    )

    # Vetor ponderado
    st.write("## Vetor Ponderado")
    weighted_df = pd.DataFrame({
        "Critério": criteria,
        "A*w": result["weighted_sum"]
    })
    st.dataframe(weighted_df.style.format({"A*w": "{:.4f}"}), use_container_width=True)

    # Consistência
    st.write("## Índices de Consistência")

    col1, col2, col3 = st.columns(3)

    col1.metric("λmax", f"{result['lambda_max']:.6f}")
    col2.metric("CI", f"{result['CI']:.6f}")

    if result["CR"] is not None:
        col3.metric("CR", f"{result['CR'] * 100:.2f}%")

        if result["CR"] <= 0.1:
            st.success("Matriz consistente (CR ≤ 10%)")
        else:
            st.warning("Matriz inconsistente (CR > 10%)")