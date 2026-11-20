"""Verrouille aussi les onglets et détails, sans déplacer le contenu."""
import streamlit as st


def interaction_lock(busy):
    if busy:
        st.html("""<script>
        if (window.brechiaUnlock) window.brechiaUnlock();
        const changed = new Map();
        function lock() {
          document.querySelectorAll('[role="tablist"], summary, a, [data-testid="stHeader"] button, [data-testid="stSidebarCollapseButton"]').forEach(el => {
            if (!changed.has(el)) { changed.set(el, el.inert); el.inert = true; }
          });
        }
        const observer = new MutationObserver(lock);
        observer.observe(document.body, {childList:true, subtree:true});
        lock();
        window.brechiaUnlock = () => {
          observer.disconnect();
          changed.forEach((value, el) => { el.inert = value; });
          delete window.brechiaUnlock;
        };
        </script>""", unsafe_allow_javascript=True)
    else:
        st.html("<script>if (window.brechiaUnlock) window.brechiaUnlock();</script>", unsafe_allow_javascript=True)
