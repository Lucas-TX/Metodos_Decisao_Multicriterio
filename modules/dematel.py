import streamlit as st
import pandas as pd

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
    # Inicialização da matriz
    # =========================
    matriz_key = "dematel_matriz"

    precisa_recriar = (
        matriz_key not in st.session_state
        or "dematel_fatores" not in st.session_state
        or st.session_state.dematel_fatores != fatores
    )

    if precisa_recriar:
        df_inicial = pd.DataFrame(0, index=fatores, columns=fatores)
        st.session_state[matriz_key] = df_inicial
        st.session_state["dematel_fatores"] = fatores

    df = st.session_state[matriz_key].copy()

    # Garante alinhamento com os fatores atuais
    df = df.reindex(index=fatores, columns=fatores, fill_value=0)

    # Diagonal sempre 0
    for i in range(len(fatores)):
        df.iat[i, i] = 0

    # =========================
    # Área central - matriz de influência
    # =========================
    st.subheader("Matriz de influência")

    st.info(
        "Informe a influência de cada fator sobre os demais. Escala: 0 = sem influência, 1 = baixa, 2 = média, 3 = alta, 4 = muito alta."
    )

    df_editado = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        key="dematel_editor",
        column_config={
            col: st.column_config.NumberColumn(
                label=col,
                min_value=0,
                max_value=4,
                step=1,
                format="%d"
            )
            for col in df.columns
        }
    )

    # =========================
    # Sanitização dos dados
    # =========================
    df_editado = pd.DataFrame(df_editado, index=fatores, columns=fatores)

    for col in df_editado.columns:
        df_editado[col] = pd.to_numeric(df_editado[col], errors="coerce").fillna(0)

    df_editado = df_editado.clip(lower=0, upper=4).astype(int)

    # Diagonal principal fixa em 0
    for i in range(len(fatores)):
        df_editado.iat[i, i] = 0

    st.session_state[matriz_key] = df_editado

    # =========================
    # Exibição final da matriz válida
    # =========================
    st.markdown("### Matriz válida para processamento")
    st.dataframe(st.session_state[matriz_key], use_container_width=True)

    # =========================
    # Dados prontos para próximas etapas
    # =========================
    st.session_state["dematel_inputs"] = {
        "fatores": fatores,
        "matriz_influencia": st.session_state[matriz_key]
    }
