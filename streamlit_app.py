import streamlit as st

# Importa as páginas com cada método
from modules import ahp

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
            set_page("dematel")

    with col2:
        if st.button("TOPSIS"):
            set_page("topsis")

        if st.button("PROMETHEE"):
            set_page("promethee")


# -----------------------------
# Roteamento
# -----------------------------
page = st.session_state.page

if page == "menu":
    show_menu()

elif page == "ahp":
    ahp.show()

elif page == "topsis":
    st.title("TOPSIS")
    if st.button("⬅ Voltar"):
        set_page("menu")

elif page == "dematel":
    st.title("DEMATEL")
    if st.button("⬅ Voltar"):
        set_page("menu")

elif page == "promethee":
    st.title("PROMETHEE")
    if st.button("⬅ Voltar"):
        set_page("menu")