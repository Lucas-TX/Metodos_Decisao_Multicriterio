import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from services.promethee_calc import run_promethee_from_streamlit_state

def show():
    st.set_page_config(page_title="PROMETHEE", layout="wide")

    st.title("PROMETHEE - Preference Ranking Organization METHod for Enrichment Evaluations")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()

    st.write(
        "O PROMETHEE é um método de análise de preferência multicritério, utilizado para ordenar alternativas com base em múltiplos critérios."
    )

    # =========================================================
    # Helpers
    # =========================================================
    PREF_FUNCTIONS = [
        "Tipo 1: Usual",
        "Tipo 2: U-Shape",
        "Tipo 3: V-Shape",
        "Tipo 4: Nível",
        "Tipo 5: V-Shape com indiferença",
        "Tipo 6: Gaussiano",
    ]

    QUAL_SCALES = {
        "5 pontos": ["Muito ruim", "Ruim", "Médio", "Bom", "Muito bom"],
        "10 pontos": ["1", "2", "3", "4", "5", "6", "7", "8", "9","10"],
        "Binário (Não/Sim)": ["Não", "Sim"],
    }

    QUAL_TO_NUM = {
        "5 pontos": {
            "Muito ruim": 1,
            "Ruim": 2,
            "Médio": 3,
            "Bom": 4,
            "Muito bom": 5,
        },
        "10 pontos": {
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
        },
    }

    PREF_EXPLANATIONS = {
        "Tipo 1: Usual": {
            "desc": "Qualquer diferença positiva já gera preferência total. Não usa limiares.",
            "params": []
        },
        "Tipo 2: U-Shape": {
            "desc": "Diferenças até q são consideradas indiferentes. Acima de q, preferência total.",
            "params": ["q"]
        },
        "Tipo 3: V-Shape": {
            "desc": "A preferência cresce linearmente até p. Acima de p, preferência total.",
            "params": ["p"]
        },
        "Tipo 4: Nível": {
            "desc": "Usa q e p. Até q há indiferença; entre q e p há preferência intermediária; acima de p há preferência total.",
            "params": ["q", "p"]
        },
        "Tipo 5: V-Shape com indiferença": {
            "desc": "Usa q e p. Até q há indiferença; de q até p a preferência cresce linearmente; acima de p há preferência total.",
            "params": ["q", "p"]
        },
        "Tipo 6: Gaussiano": {
            "desc": "Usa s. A preferência cresce suavemente segundo uma curva gaussiana.",
            "params": ["s"]
        },
    }

    def default_criterion(i: int):
        return {
            "name": f"Critério {i+1}",
            "tipo": "Quantitativo",
            "escala_qualitativa": "5 pontos",
            "objetivo": "Maximização",
            "peso": 1.0,
            "funcao_pref": "Tipo 1: Usual",
            "q": 0.0,
            "p": 1.0,
            "s": 1.0,
        }

    def default_alternative(i: int):
        return f"Alternativa {i+1}"

    def sync_counts(num_criteria: int, num_alternatives: int):
        if "criteria" not in st.session_state:
            st.session_state.criteria = [default_criterion(i) for i in range(num_criteria)]
        else:
            current = len(st.session_state.criteria)
            if num_criteria > current:
                for i in range(current, num_criteria):
                    st.session_state.criteria.append(default_criterion(i))
            elif num_criteria < current:
                st.session_state.criteria = st.session_state.criteria[:num_criteria]

        if "alternatives" not in st.session_state:
            st.session_state.alternatives = [default_alternative(i) for i in range(num_alternatives)]
        else:
            current = len(st.session_state.alternatives)
            if num_alternatives > current:
                for i in range(current, num_alternatives):
                    st.session_state.alternatives.append(default_alternative(i))
            elif num_alternatives < current:
                st.session_state.alternatives = st.session_state.alternatives[:num_alternatives]

    def get_scale_options(criterion):
        if criterion["tipo"] == "Binário":
            return QUAL_SCALES["Binário (Não/Sim)"]
        if criterion["tipo"] == "Qualitativo":
            return QUAL_SCALES.get(criterion["escala_qualitativa"], QUAL_SCALES["5 pontos"])
        return None

    def get_default_value(criterion):
        if criterion["tipo"] == "Quantitativo":
            return 0.0
        if criterion["tipo"] == "Binário":
            return "Não"
        opts = get_scale_options(criterion)
        return opts[0] if opts else ""

    def normalize_value(value, criterion):
        if criterion["tipo"] == "Quantitativo":
            try:
                return float(value)
            except Exception:
                return 0.0

        if criterion["tipo"] == "Binário":
            return "Sim" if str(value) == "Sim" else "Não"

        opts = get_scale_options(criterion)
        return value if value in opts else (opts[0] if opts else "")

    def align_matrix():
        alt_names = st.session_state.alternatives
        criteria = st.session_state.criteria

        if "decision_df" not in st.session_state:
            df = pd.DataFrame(index=alt_names)
            for c in criteria:
                df[c["name"]] = [get_default_value(c)] * len(alt_names)
            st.session_state.decision_df = df
            return

        old_df = st.session_state.decision_df.copy()
        new_df = pd.DataFrame(index=alt_names)

        for c in criteria:
            cname = c["name"]

            if cname in old_df.columns:
                col = old_df[cname].reindex(alt_names)
                col = col.apply(lambda x: normalize_value(x, c))
                new_df[cname] = col
            else:
                new_df[cname] = [get_default_value(c)] * len(alt_names)

        st.session_state.decision_df = new_df

    def build_numeric_matrix(df):
        numeric_df = pd.DataFrame(index=df.index)

        for c in st.session_state.criteria:
            cname = c["name"]

            if c["tipo"] == "Quantitativo":
                numeric_df[cname] = pd.to_numeric(df[cname], errors="coerce").fillna(0.0).astype(float)

            elif c["tipo"] == "Binário":
                numeric_df[cname] = df[cname].map({"Não": 0.0, "Sim": 1.0}).astype(float)

            elif c["tipo"] == "Qualitativo":
                escala = c["escala_qualitativa"]
                mapa = QUAL_TO_NUM[escala]
                numeric_df[cname] = df[cname].map(mapa).astype(float)

        return numeric_df

    def preference_curve_values(func_name, q=0.0, p=1.0, s=1.0):
        x = np.linspace(
            0,
            max(
                10,
                p * 1.3 if p else 10,
                q * 1.3 if q else 10,
                s * 3 if s else 10
            ),
            400
        )

        if func_name == "Tipo 1: Usual":
            y = np.where(x > 0, 1.0, 0.0)

        elif func_name == "Tipo 2: U-Shape":
            y = np.where(x <= q, 0.0, 1.0)

        elif func_name == "Tipo 3: V-Shape":
            pp = max(p, 1e-9)
            y = np.where(x <= 0, 0.0, np.where(x < pp, x / pp, 1.0))

        elif func_name == "Tipo 4: Nível":
            qq = q
            pp = max(p, qq + 1e-9)
            y = np.where(x <= qq, 0.0, np.where(x <= pp, 0.5, 1.0))

        elif func_name == "Tipo 5: V-Shape com indiferença":
            qq = q
            pp = max(p, qq + 1e-9)
            y = np.where(x <= qq, 0.0, np.where(x < pp, (x - qq) / (pp - qq), 1.0))

        elif func_name == "Tipo 6: Gaussiano":
            ss = max(s, 1e-9)
            y = 1 - np.exp(-(x ** 2) / (2 * ss ** 2))

        else:
            y = np.zeros_like(x)

        return x, np.clip(y, 0, 1)

    def plot_preference_function(func_name, q=0.0, p=1.0, s=1.0):
        x, y = preference_curve_values(func_name, q, p, s)

        fig, ax = plt.subplots(figsize=(6, 3.2))
        ax.plot(x, y, linewidth=2)
        ax.set_xlabel("Diferença d")
        ax.set_ylabel("P(d)")
        ax.set_ylim(-0.02, 1.02)
        ax.set_title(func_name)
        ax.grid(True, alpha=0.25)

        if "q" in PREF_EXPLANATIONS[func_name]["params"]:
            ax.axvline(q, color="orange", linestyle="--", alpha=0.8, label="q")

        if "p" in PREF_EXPLANATIONS[func_name]["params"]:
            ax.axvline(p, color="green", linestyle="--", alpha=0.8, label="p")

        if "s" in PREF_EXPLANATIONS[func_name]["params"]:
            ax.axvline(s, color="purple", linestyle="--", alpha=0.8, label="s")

        if PREF_EXPLANATIONS[func_name]["params"]:
            ax.legend()

        fig.tight_layout()
        return fig

    # =========================================================
    # Sidebar
    # =========================================================
    st.sidebar.title("Configuração do problema")

    num_criteria = st.sidebar.number_input(
        "Quantidade de critérios",
        min_value=1,
        max_value=20,
        value=3,
        step=1
    )

    num_alternatives = st.sidebar.number_input(
        "Quantidade de alternativas",
        min_value=1,
        max_value=50,
        value=4,
        step=1
    )

    sync_counts(num_criteria, num_alternatives)

    st.sidebar.markdown("### Nomes dos critérios")
    for i in range(num_criteria):
        st.session_state.criteria[i]["name"] = st.sidebar.text_input(
            f"Critério {i+1}",
            value=st.session_state.criteria[i]["name"],
            key=f"crit_name_{i}"
        )

    st.sidebar.markdown("### Nomes das alternativas")
    for i in range(num_alternatives):
        st.session_state.alternatives[i] = st.sidebar.text_input(
            f"Alternativa {i+1}",
            value=st.session_state.alternatives[i],
            key=f"alt_name_{i}"
        )

    align_matrix()

    # =========================================================
    # Main
    # =========================================================
    st.title("Configuração da Interface")
    st.caption("UI para cadastro de critérios, alternativas, funções de preferência e matriz de decisão.")

    tab_labels = [c["name"] for c in st.session_state.criteria]
    tabs = st.tabs(tab_labels)

    for i, tab in enumerate(tabs):
        criterion = st.session_state.criteria[i]

        with tab:
            st.subheader(f"Configuração: {criterion['name']}")

            c1, c2, c3 = st.columns([1, 1, 1])

            with c1:
                criterion["tipo"] = st.selectbox(
                    "Tipo do critério",
                    ["Quantitativo", "Binário", "Qualitativo"],
                    index=["Quantitativo", "Binário", "Qualitativo"].index(criterion["tipo"]),
                    key=f"tipo_{i}"
                )

            with c2:
                criterion["objetivo"] = st.radio(
                    "Objetivo",
                    ["Maximização", "Minimização"],
                    index=["Maximização", "Minimização"].index(criterion["objetivo"]),
                    horizontal=True,
                    key=f"obj_{i}"
                )

            with c3:
                criterion["peso"] = st.number_input(
                    "Peso",
                    min_value=0.0,
                    value=float(criterion["peso"]),
                    step=0.1,
                    key=f"peso_{i}"
                )

            if criterion["tipo"] == "Qualitativo":
                criterion["escala_qualitativa"] = st.selectbox(
                    "Escala qualitativa",
                    ["5 pontos", "10 pontos"],
                    index=["5 pontos", "10 pontos"].index(
                        criterion["escala_qualitativa"]
                        if criterion["escala_qualitativa"] in ["5 pontos", "10 pontos"]
                        else "5 pontos"
                    ),
                    key=f"escala_qual_{i}"
                )
                st.write("Níveis:", ", ".join(get_scale_options(criterion)))

            elif criterion["tipo"] == "Binário":
                st.write("Escala binária: Não / Sim")

            st.markdown("---")
            st.markdown("### Função de preferência")

            criterion["funcao_pref"] = st.selectbox(
                "Escolha a função de preferência",
                PREF_FUNCTIONS,
                index=PREF_FUNCTIONS.index(criterion["funcao_pref"]),
                key=f"pref_fn_{i}"
            )

            explanation = PREF_EXPLANATIONS[criterion["funcao_pref"]]
            st.info(explanation["desc"])

            params = explanation["params"]
            pcol1, pcol2, pcol3 = st.columns(3)

            with pcol1:
                if "q" in params:
                    criterion["q"] = st.number_input(
                        "Limiar de indiferença (q)",
                        min_value=0.0,
                        value=float(criterion["q"]),
                        step=0.1,
                        key=f"q_{i}"
                    )
                else:
                    criterion["q"] = float(criterion.get("q", 0.0))

            with pcol2:
                if "p" in params:
                    criterion["p"] = st.number_input(
                        "Limiar de preferência (p)",
                        min_value=0.0,
                        value=float(max(criterion["p"], criterion["q"])) if "q" in params else float(criterion["p"]),
                        step=0.1,
                        key=f"p_{i}"
                    )
                else:
                    criterion["p"] = float(criterion.get("p", 1.0))

            with pcol3:
                if "s" in params:
                    criterion["s"] = st.number_input(
                        "Limiar gaussiano (s)",
                        min_value=0.0001,
                        value=float(max(criterion["s"], 0.0001)),
                        step=0.1,
                        key=f"s_{i}"
                    )
                else:
                    criterion["s"] = float(criterion.get("s", 1.0))

            if "q" in params and "p" in params and criterion["p"] < criterion["q"]:
                st.warning("Ajuste recomendado: p deve ser maior ou igual a q.")

            fig = plot_preference_function(
                criterion["funcao_pref"],
                q=float(criterion["q"]),
                p=float(criterion["p"]),
                s=float(criterion["s"])
            )
            st.pyplot(fig, clear_figure=True)

    # Realinha a matriz após possíveis mudanças de tipo/escala
    align_matrix()

    # =========================================================
    # Matriz de decisão
    # =========================================================
    st.markdown("---")
    st.header("Matriz de decisão")

    criterios = st.session_state.criteria
    alternativas = st.session_state.alternatives
    criterio_nomes = [c["name"] for c in criterios]

    df = st.session_state.decision_df.reindex(
        index=alternativas,
        columns=criterio_nomes
    ).copy()

    st.info(
        "Informe a avaliação de cada alternativa em cada critério."
    )

    header_cols = st.columns([1.2] + [1] * len(criterios))
    header_cols[0].markdown("**Alternativa \\ Critério**")

    for j, crit in enumerate(criterios):
        header_cols[j + 1].markdown(f"**{crit['name']}**")

    for i, alternativa in enumerate(alternativas):
        row_cols = st.columns([1.2] + [1] * len(criterios))
        row_cols[0].markdown(f"**{alternativa}**")

        for j, crit in enumerate(criterios):
            cell_key = f"promethee_cell_{i}_{j}"
            valor_atual = normalize_value(df.iat[i, j], crit)

            if cell_key not in st.session_state:
                st.session_state[cell_key] = valor_atual
            else:
                st.session_state[cell_key] = normalize_value(st.session_state[cell_key], crit)

            if crit["tipo"] == "Quantitativo":
                valor = row_cols[j + 1].number_input(
                    label=f"{alternativa}-{crit['name']}",
                    value=float(st.session_state[cell_key]),
                    step=0.1,
                    key=cell_key,
                    label_visibility="collapsed"
                )
                df.iat[i, j] = float(valor)

            elif crit["tipo"] == "Binário":
                opcoes = QUAL_SCALES["Binário (Não/Sim)"]
                valor = row_cols[j + 1].selectbox(
                    label=f"{alternativa}-{crit['name']}",
                    options=opcoes,
                    index=opcoes.index(st.session_state[cell_key]),
                    key=cell_key,
                    label_visibility="collapsed"
                )
                df.iat[i, j] = valor

            elif crit["tipo"] == "Qualitativo":
                opcoes = get_scale_options(crit)
                valor = row_cols[j + 1].selectbox(
                    label=f"{alternativa}-{crit['name']}",
                    options=opcoes,
                    index=opcoes.index(st.session_state[cell_key]),
                    key=cell_key,
                    label_visibility="collapsed"
                )
                df.iat[i, j] = valor

    st.session_state.decision_df = df.copy()
    st.session_state.decision_df_numeric = build_numeric_matrix(df)

    # =========================================================
    # Resumo
    # =========================================================
    st.markdown("---")
    st.subheader("Resumo da configuração")

    summary_rows = []
    for c in st.session_state.criteria:
        summary_rows.append({
            "Critério": c["name"],
            "Tipo": c["tipo"],
            "Objetivo": c["objetivo"],
            "Peso": c["peso"],
            "Escala qualitativa": c["escala_qualitativa"] if c["tipo"] == "Qualitativo" else None,
            "Função": c["funcao_pref"],
            "q": c["q"] if "q" in PREF_EXPLANATIONS[c["funcao_pref"]]["params"] else None,
            "p": c["p"] if "p" in PREF_EXPLANATIONS[c["funcao_pref"]]["params"] else None,
            "s": c["s"] if "s" in PREF_EXPLANATIONS[c["funcao_pref"]]["params"] else None,
        })

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    st.subheader("Resultado do PROMETHEE")

    executar_promethee = st.button("Executar PROMETHEE", type="primary")

    if executar_promethee:
        try:
            resultado = run_promethee_from_streamlit_state(
                criteria=st.session_state.criteria,
                decision_df_numeric=st.session_state.decision_df_numeric
            )

            st.success("PROMETHEE executado com sucesso.")
            st.dataframe(resultado["ranking"], use_container_width=True)
            st.dataframe(resultado["flows"], use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao executar o PROMETHEE: {e}")