import streamlit as st
import pandas as pd
import numpy as np

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
        data=np.zeros((qtd_criterios, qtd_alternativas)),
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
    # BOTÃO FUTURO PARA EXECUÇÃO
    # =========================

    executar = st.button("Executar TOPSIS", type="primary")

    if executar:
        st.info("Nesta etapa, o cálculo TOPSIS ainda não foi implementado.")
