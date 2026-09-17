import streamlit as st

st.title("Min første Streamlit-app")

navn = st.text_input("Hva heter du?")

if navn:
    st.write(f"Hei, {navn}!")