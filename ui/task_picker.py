import streamlit as st
from scenarios.tasks import TASKS, task_id

def select_task(catalog, key):
    task = st.selectbox("Tâche à évaluer", list(TASKS), format_func=TASKS.get, key=key)
    return [s for s in catalog if task_id(s) == task]
