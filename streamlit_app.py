import streamlit as st

# Importa as páginas com cada método
from modules import ahp,dematel, topsis

# -----------------------------
# Estado inicial
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "menu"


def set_page(page):
    st.session_state.page = page


# -----------------------------
# Menu principal
# -----------------------------
def show_menu():
    st.title("📊 Métodos Multicritério")

    st.write("Selecione o método:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("AHP"):
            st.session_state.page = "ahp"
            st.rerun()

        if st.button("DEMATEL"):
            st.session_state.page = "dematel"
            st.rerun()

    with col2:
        if st.button("TOPSIS"):
            st.session_state.page = "topsis"
            st.rerun()

        if st.button("PROMETHEE"):
            st.session_state.page = "promethee"
            st.rerun()


# -----------------------------
# Roteamento
# -----------------------------
page = st.session_state.page

if page == "menu":
    show_menu()

elif page == "ahp":
    ahp.show()

elif page == "topsis":
    topsis.show()

elif page == "dematel":
    dematel.show()

elif page == "promethee":
    st.title("PROMETHEE")
    if st.button("⬅ Voltar"):
        set_page("menu")