"""Point d’entrée : python app.py ou python -m streamlit run app.py."""
from pathlib import Path
import subprocess
import sys


def launch():
    """Démarre Streamlit depuis la racine, quel que soit le dossier courant."""
    root = Path(__file__).resolve().parent
    command = [sys.executable, "-m", "streamlit", "run", str(root / "app.py"),
               "--server.address=127.0.0.1", "--server.port=8501", "--server.headless=false"]
    try:
        # Refuse les courriels promotionnels proposés au premier lancement.
        return subprocess.run(command, cwd=root, input="\n", text=True, check=False).returncode
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        raise SystemExit("Dépendances manquantes : lancez python -m pip install -r requirements.txt")
    if get_script_run_ctx(suppress_warning=True) is None:
        raise SystemExit(launch())

import streamlit as st
from ui.styles import header
from ui.real_lab import real_laboratory
from ui.pages import dashboard, laboratory, comparison, logs, methodology

st.set_page_config(page_title="BrèchIA · Laboratoire", page_icon="🛡️", layout="wide")
header()
st.sidebar.html('<div class="lab-wordmark">BrèchIA</div>')
st.sidebar.caption("Laboratoire de sécurité des agents d’IA")
NAV_LABELS = {"Tableau de bord": "Vue d’ensemble", "Laboratoire": "Simulateur pédagogique", "Comparaison": "Campagnes simulées", "Historique et journaux": "Journaux du simulateur", "Méthodologie et éthique": "Protocole et éthique", "Modèle réel (local)": "Expériences avec un modèle"}
st.sidebar.divider()
page = st.sidebar.radio("Espace de travail", list(NAV_LABELS), format_func=NAV_LABELS.get, key="navigation")
st.sidebar.divider()
with st.sidebar.expander("Quel espace choisir ?"):
    st.write("**Simulateur** : comprendre les mécanismes avec des résultats préparés.\n\n**Modèle réel** : observer les réponses générées par une IA locale.")
st.sidebar.caption("Projet pédagogique indépendant · INF5163\n\nAucune affiliation officielle à l’UQO. Aucun service tiers testé.")
{"Tableau de bord": dashboard, "Laboratoire": laboratory, "Comparaison": comparison,
 "Modèle réel (local)": real_laboratory, "Historique et journaux": logs, "Méthodologie et éthique": methodology}[page]()
