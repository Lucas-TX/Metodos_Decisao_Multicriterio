import streamlit as st

def show():
    st.title("LPA2V - Lógica Paraconsistente Anotada com Dois Valores")

    if st.button("⬅ Voltar"):
        st.session_state.page = "menu"
        st.rerun()
    
    st.write("Em desenvolvimento...")