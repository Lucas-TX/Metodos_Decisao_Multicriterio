import streamlit as st
import pandas as pd
import numpy as np
from services.topsis_calc import calcular_topsis

def show():

    st.title("TOPSIS - Technique for Order of Preference by Similarity to Ideal Solution")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()

    st.write(
        "O TOPSIS é um método de tomada de decisão multicritério que classifica as alternativas com base na distância para a solução ideal positiva e negativa."
    )

    st.info(
        "Informe os critérios, pesos, tipos de critério e alternativas na barra lateral. "
        "Depois, preencha a matriz de decisão."
    )

    # =========================
    # SIDEBAR
    # =========================

    st.sidebar.header("Configuração do TOPSIS")

    qtd_criterios = st.sidebar.number_input(
        "Quantidade de critérios",
        min_value=2,
        value=4,
        step=1
    )

    qtd_alternativas = st.sidebar.number_input(
        "Quantidade de alternativas",
        min_value=2,
        value=3,
        step=1
    )

    st.sidebar.divider()

    # =========================
    # CRITÉRIOS
    # =========================

    st.sidebar.subheader("Critérios")

    criterios = []
    pesos = []
    tipos_criterios = []

    for i in range(qtd_criterios):
        st.sidebar.markdown(f"**Critério {i + 1}**")

        nome_criterio = st.sidebar.text_input(
            "Nome do critério",
            value=f"Critério {i + 1}",
            key=f"criterio_nome_{i}"
        )

        peso = st.sidebar.number_input(
            "Peso",
            min_value=0.0,
            value=1.0,
            step=0.5,
            max_value=10.0,
            key=f"criterio_peso_{i}"
        )

        tipo = st.sidebar.selectbox(
            "Tipo",
            options=["Maximização", "Minimização"],
            key=f"criterio_tipo_{i}"
        )

        criterios.append(nome_criterio)
        pesos.append(peso)
        tipos_criterios.append(tipo)

        st.sidebar.divider()

    # =========================
    # ALTERNATIVAS
    # =========================

    st.sidebar.subheader("Alternativas")

    alternativas = []

    for i in range(qtd_alternativas):
        nome_alternativa = st.sidebar.text_input(
            f"Nome da alternativa {i + 1}",
            value=f"Alternativa {i + 1}",
            key=f"alternativa_nome_{i}"
        )

        alternativas.append(nome_alternativa)

    # =========================
    # ÁREA CENTRAL
    # =========================

    st.subheader("Matriz de decisão")

    matriz_inicial = pd.DataFrame(
        data=np.ones((qtd_criterios, qtd_alternativas)),
        index=criterios,
        columns=alternativas
    )
    
    column_config = {
        alternativa: st.column_config.NumberColumn(
            label=alternativa,
            min_value=1.0,
            max_value=10.0,
            step=0.5,
            required=True
        )
        for alternativa in alternativas
    }

    matriz_decisao = st.data_editor(
        matriz_inicial,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        key="matriz_decisao"
    )


    # =========================
    # RESUMO DAS CONFIGURAÇÕES
    # =========================

    st.subheader("Resumo da configuração")

    df_configuracao = pd.DataFrame({
        "Critério": criterios,
        "Peso": pesos,
        "Tipo": tipos_criterios
    })

    st.dataframe(
        df_configuracao,
        use_container_width=True
    )

    # =========================
    # EXECUÇÃO E VISUALIZAÇÃO DOS RESULTADOS
    # =========================

    st.subheader("Resultado do TOPSIS")

    executar_topsis = st.button("Executar TOPSIS", type="primary")

    if executar_topsis:
        resultado = calcular_topsis(
            matrix=matriz_decisao.values,
            weights=pesos,
            criteria_types=tipos_criterios
        )

        st.session_state["topsis_resultado"] = resultado
        st.session_state["topsis_criterios"] = criterios
        st.session_state["topsis_alternativas"] = alternativas
        st.session_state["topsis_pesos"] = pesos
        st.session_state["topsis_tipos_criterios"] = tipos_criterios

    if "topsis_resultado" in st.session_state:

        resultado = st.session_state["topsis_resultado"]
        criterios = st.session_state["topsis_criterios"]
        alternativas = st.session_state["topsis_alternativas"]
        pesos = st.session_state["topsis_pesos"]
        tipos_criterios = st.session_state["topsis_tipos_criterios"]

        aba_final, aba_pesos, aba_normalizacao, aba_ponderada, aba_ideais, aba_distancias = st.tabs([
            "Resultado Final",
            "Pesos",
            "Normalização",
            "Matriz Ponderada",
            "Soluções Ideais",
            "Distâncias"
        ])

        # =========================
        # RESULTADO FINAL
        # =========================

        with aba_final:
            df_resultado = pd.DataFrame({
                "Alternativa": alternativas,
                "Ranking": resultado["ranking_positions"],
                "Score TOPSIS": resultado["scores"],
                "Distância Ideal Positiva": resultado["distance_positive"],
                "Distância Ideal Negativa": resultado["distance_negative"]                
            })

            df_resultado = df_resultado.sort_values("Ranking")

            melhor_alternativa = df_resultado.iloc[0]["Alternativa"]
            melhor_score = df_resultado.iloc[0]["Score TOPSIS"]

            st.metric(
                label="Melhor alternativa",
                value=melhor_alternativa,
                delta=f"Score: {melhor_score:.4f}"
            )

            st.subheader("Ranking final")

            st.dataframe(
                df_resultado,
                use_container_width=True
            )

            st.subheader("Gráfico do Score TOPSIS")

            st.bar_chart(
                df_resultado.set_index("Alternativa")["Score TOPSIS"]
            )

        # =========================
        # PESOS
        # =========================

        with aba_pesos:
            df_pesos = pd.DataFrame({
                "Critério": criterios,
                "Peso Original": resultado["weights"],
                "Peso Normalizado": resultado["normalized_weights"]
            })

            st.subheader("Pesos")

            st.dataframe(
                df_pesos,
                use_container_width=True
            )
       
        # =========================
        # NORMALIZAÇÃO
        # =========================

        with aba_normalizacao:
            df_normalizacao = pd.DataFrame({
                "Critério": criterios,
                "Soma dos Quadrados": resultado["row_square_sums"],
                "Raiz da Soma dos Quadrados": resultado["row_norms"]
            })

            st.subheader("Cálculo da normalização")

            st.dataframe(
                df_normalizacao,
                use_container_width=True
            )

            df_matriz_normalizada = pd.DataFrame(
                resultado["normalized_matrix"],
                index=criterios,
                columns=alternativas
            )

            st.subheader("Matriz normalizada")

            st.dataframe(
                df_matriz_normalizada,
                use_container_width=True
            )

        # =========================
        # MATRIZ PONDERADA
        # =========================

        with aba_ponderada:
            df_matriz_ponderada = pd.DataFrame(
                resultado["weighted_normalized_matrix"],
                index=criterios,
                columns=alternativas
            )

            st.subheader("Matriz normalizada ponderada")

            st.dataframe(
                df_matriz_ponderada,
                use_container_width=True
            )

        # =========================
        # SOLUÇÕES IDEAIS
        # =========================

        with aba_ideais:
            df_ideais = pd.DataFrame({
                "Critério": criterios,
                "Tipo": tipos_criterios,
                "Ideal Positiva": resultado["ideal_positive"],
                "Ideal Negativa": resultado["ideal_negative"]
            })

            st.subheader("Soluções ideais")

            st.dataframe(
                df_ideais,
                use_container_width=True
            )

        # =========================
        # DISTÂNCIAS
        # =========================

        with aba_distancias:
            df_distancias = pd.DataFrame({
                "Alternativa": alternativas,
                "Ranking": resultado["ranking_positions"],
                "Score TOPSIS": resultado["scores"],
                "Distância Ideal Positiva": resultado["distance_positive"],
                "Distância Ideal Negativa": resultado["distance_negative"]               
            })

            df_distancias = df_distancias.sort_values("Ranking")

            st.subheader("Distâncias e scores")

            st.dataframe(
                df_distancias,
                use_container_width=True
            )


