import streamlit as st


def french_multiselect(label, options, key, format_func=str, disabled=False):
    return st.multiselect(label, options, default=[], key=key,
                          format_func=format_func, placeholder="Choisir les options", select_all=True, disabled=disabled)
