import streamlit as st

def show():
    st.title("Electre TRI - Elimination and Choice Expressing Reality")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()
    
    st.write("Em desenvolvimento...")