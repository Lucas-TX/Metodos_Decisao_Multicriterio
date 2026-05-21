import streamlit as st

def show():

    st.title("DEMATEL - Decision Making Trial and Evaluation Laboratory")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()