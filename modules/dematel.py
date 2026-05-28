import streamlit as st
import pandas as pd
import numpy as np
from services.dematel_calc import calcular_dematel
import plotly.graph_objects as go

def show():

    st.title("DEMATEL - Decision Making Trial and Evaluation Laboratory")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()

    st.write(
        "O DEMATEL é um método de análise de relações causais entre fatores, utilizado para identificar e visualizar as influências entre eles."
    )

    # =========================
    # Sidebar - definição dos fatores
    # =========================
    st.sidebar.header("Fatores")

    qtd_fatores = st.sidebar.number_input(
        "Quantidade de fatores",
        min_value=2,
        max_value=20,
        value=4,
        step=1,
        key="dematel_qtd_fatores"
    )

    fatores = []
    for i in range(qtd_fatores):
        nome = st.sidebar.text_input(
            f"Fator {i+1}",
            value=f"F{i+1}",
            key=f"dematel_fator_{i}"
        ).strip()

        if nome == "":
            nome = f"F{i+1}"

        fatores.append(nome)

    # Evita nomes duplicados
    fatores_unicos = []
    nomes_usados = {}

    for nome in fatores:
        if nome not in nomes_usados:
            nomes_usados[nome] = 1
            fatores_unicos.append(nome)
        else:
            nomes_usados[nome] += 1
            fatores_unicos.append(f"{nome}_{nomes_usados[nome]}")

    fatores = fatores_unicos


    # =========================
    # Inicialização / recriação da matriz com base nos fatores do sidebar
    # =========================
    matriz_key = "dematel_matriz"
    fatores_key = "dematel_fatores"

    if (
        fatores_key not in st.session_state
        or st.session_state[fatores_key] != fatores
    ):
        st.session_state[fatores_key] = fatores
        st.session_state[matriz_key] = pd.DataFrame(
            0,
            index=fatores,
            columns=fatores,
            dtype=float
        )

    df = st.session_state[matriz_key].reindex(
        index=fatores,
        columns=fatores,
        fill_value=0
    ).copy()

    # Garante diagonal principal = 0
    for i in range(len(fatores)):
        df.iat[i, i] = 0.0

    # =========================
    # Matriz de influência
    # =========================
    st.subheader("Matriz de influência")

    st.info(
        "Informe a influência de cada fator sobre os demais.\n"
        "\nEscala: 0 = sem influência, 1 = baixa, 2 = média, 3 = alta, 4 = muito alta."
    )

    header_cols = st.columns([1] + [1] * len(fatores))
    header_cols[0].markdown("**Influência de \\ sobre**")
    for j, fator_col in enumerate(fatores):
        header_cols[j + 1].markdown(f"**{fator_col}**")

    for i, fator_linha in enumerate(fatores):
        row_cols = st.columns([1] + [1] * len(fatores))
        row_cols[0].markdown(f"**{fator_linha}**")

        for j, fator_col in enumerate(fatores):
            cell_key = f"dematel_cell_{i}_{j}"

            if cell_key not in st.session_state:
                st.session_state[cell_key] = float(df.iat[i, j])

            if i == j:
                st.session_state[cell_key] = 0.0
                row_cols[j + 1].number_input(
                    label=f"{fator_linha}->{fator_col}",
                    min_value=0.0,
                    max_value=0.0,
                    value=0.0,
                    step=0.5,
                    disabled=True,
                    key=cell_key,
                    label_visibility="collapsed"
                )
                df.iat[i, j] = 0
            else:
                valor = row_cols[j + 1].number_input(
                    label=f"{fator_linha}->{fator_col}",
                    min_value=0.0,
                    max_value=4.0,
                    value=float(st.session_state[cell_key]),
                    step=0.5,
                    key=cell_key,
                    label_visibility="collapsed"
                )
                df.iat[i, j] = float(valor)

    # Garante novamente diagonal principal = 0
    for i in range(len(fatores)):
        df.iat[i, i] = 0

    st.session_state[matriz_key] = df

    # =========================
    # RESULTADOS
    # =========================

    st.subheader("Resultado do DEMATEL")

    executar_dematel = st.button("Executar DEMATEL", type="primary")

    if executar_dematel:
        try:
            resultado = calcular_dematel(df.values)

            fatores_resultado = fatores

            # Matrizes
            z_df = pd.DataFrame(
                resultado["z_matrix"],
                index=fatores_resultado,
                columns=fatores_resultado
            )

            d_df = pd.DataFrame(
                resultado["normalized_matrix"],
                index=fatores_resultado,
                columns=fatores_resultado
            )

            i_menos_d_df = pd.DataFrame(
                resultado["identity_minus_normalized"],
                index=fatores_resultado,
                columns=fatores_resultado
            )

            inv_i_menos_d_df = pd.DataFrame(
                resultado["inverse_identity_minus_normalized"],
                index=fatores_resultado,
                columns=fatores_resultado
            )

            t_df = pd.DataFrame(
                resultado["total_relation_matrix"],
                index=fatores_resultado,
                columns=fatores_resultado
            )

            threshold_matrix_df = pd.DataFrame(
                resultado["threshold_matrix"],
                index=fatores_resultado,
                columns=fatores_resultado
            )

            # Resumo
            resumo_df = pd.DataFrame({
                "Fator": fatores_resultado,
                "r": resultado["r"],
                "c": resultado["c"],
                "r+c": resultado["prominence"],
                "r-c": resultado["relation"],
                "Classificação": resultado["classification"]
            }).set_index("Fator")

            
            # Coordenadas dos fatores
            x = resultado["coordinates"][:, 0]   # r + c
            y = resultado["coordinates"][:, 1]   # r - c
            threshold_matrix = resultado["threshold_matrix"]

            st.success("DEMATEL executado com sucesso!")

            # Métricas principais
            col1, col2 = st.columns(2)
            col1.metric("Lambda (λ)", f"{resultado['lambda_value']:.6f}")
            col2.metric("Alfa (α)", f"{resultado['alpha']:.6f}")

            # Abas
            aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
                "Resumo",
                "Matriz Z",
                "Matriz D",
                "Matriz I-D",
                "Matriz (I-D)^-1",
                "Matriz T"
            ])

            with aba1:
                st.markdown("### Vetores e indicadores")
                st.dataframe(
                    resumo_df.style.format({
                        "r": "{:.6f}",
                        "c": "{:.6f}",
                        "r+c": "{:.6f}",
                        "r-c": "{:.6f}"
                    }),
                    use_container_width=True
                )

                st.markdown("### Mapa de Influência")
                fig = go.Figure()
  
                # Linhas de referência
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                fig.add_vline(x=float(np.mean(x)), line_dash="dash", line_color="gray")

                # Arestas com base na matriz T filtrada
                for i in range(len(fatores_resultado)):
                    for j in range(len(fatores_resultado)):
                        if i != j and threshold_matrix[i, j] > 0:
                            fig.add_trace(
                                go.Scatter(
                                    x=[x[i], x[j]],
                                    y=[y[i], y[j]],
                                    mode="lines",
                                    line=dict(width=1.5, color="rgba(120,120,120,0.6)"),
                                    hoverinfo="text",
                                    text=(
                                        f"{fatores_resultado[i]} → {fatores_resultado[j]}"
                                        f"<br>Influência: {threshold_matrix[i, j]:.6f}"
                                    ),
                                    showlegend=False
                                )
                            )

                # Pontos dos fatores
                cores = [
                    "red" if rel > 0 else "blue" if rel < 0 else "gray"
                    for rel in resultado["relation"]
                ]

                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        mode="markers+text",
                        text=fatores_resultado,
                        textposition="top center",
                        marker=dict(
                            size=12,
                            color=cores,
                            line=dict(width=1, color="black")
                        ),
                        hovertemplate=(
                            "<b>%{text}</b><br>"
                            "r+c: %{x:.6f}<br>"
                            "r-c: %{y:.6f}<extra></extra>"
                        ),
                        showlegend=False
                    )
                )

                fig.update_layout(
                    xaxis_title="r + c",
                    yaxis_title="r - c",
                    height=650,
                    margin=dict(l=20, r=20, t=20, b=20)
                )

                st.plotly_chart(fig, use_container_width=True)

            with aba2:
                st.markdown("### Matriz Z")
                st.dataframe(
                    z_df.style.format("{:.6f}"),
                    use_container_width=True
                )

            with aba3:
                st.markdown("### Matriz D")
                st.dataframe(
                    d_df.style.format("{:.6f}"),
                    use_container_width=True
                )

            with aba4:
                st.markdown("### Matriz I - D")
                st.dataframe(
                    i_menos_d_df.style.format("{:.6f}"),
                    use_container_width=True
                )

            with aba5:
                st.markdown("### Matriz (I - D)^-1")
                st.dataframe(
                    inv_i_menos_d_df.style.format("{:.6f}"),
                    use_container_width=True
                )

            with aba6:
                st.markdown("### Matriz T")
                st.dataframe(
                    t_df.style.format("{:.6f}"),
                    use_container_width=True
                )

                st.markdown("### Matriz T filtrada por Alfa (α)")

                st.dataframe(
                    threshold_matrix_df.style.format("{:.6f}"),
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Erro ao executar o DEMATEL: {e}")