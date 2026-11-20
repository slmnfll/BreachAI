"""Champ de recherche local actualisé après une courte pause de saisie."""
import streamlit as st

_component = st.components.v2.component(
    "brechia_live_search",
    html='<label for="query">Rechercher dans les expériences</label><input id="query" type="search" placeholder="A 01, réunion, Alice, 2026-11-19…" autocomplete="off" />',
    css="""label {display:block;font:500 15px sans-serif;margin-bottom:8px;color:var(--st-text-color);}
    input {box-sizing:border-box;width:100%;height:42px;border:1px solid #8ba7b8;border-radius:8px;padding:8px 12px;font:16px sans-serif;color:var(--st-text-color);background:var(--st-secondary-background-color);}
    input:focus {outline:2px solid #005f85;outline-offset:1px;}""",
    js="""export default function(component) {
      const input = component.parentElement.querySelector('input');
      if (!input.dataset.initialized) {
        input.value = component.data.initial || '';
        input.dataset.initialized = 'true';
      }
      let timer;
      const update = () => {
        clearTimeout(timer);
        timer = setTimeout(() => component.setStateValue('query', input.value), 250);
      };
      input.addEventListener('input', update);
      return () => { clearTimeout(timer); input.removeEventListener('input', update); };
    }""",
)

def live_search(key):
    result = _component(key=key + "_input", data={"initial": st.session_state.get(key, "")},
                        default={"query": st.session_state.get(key, "")},
                        on_query_change=lambda: None)
    query = result.query or ""
    st.session_state[key] = query
    return query
