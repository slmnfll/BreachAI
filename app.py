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
from ui.pages import dashboard, laboratory, comparison, logs, methodology

st.set_page_config(page_title="BrèchIA · Laboratoire", page_icon="🛡️", layout="wide")
header()
st.sidebar.title("BrèchIA")
st.sidebar.caption("Sécurité des agents d’IA")
page = st.sidebar.radio("Navigation", ["Tableau de bord", "Laboratoire", "Comparaison", "Historique et journaux", "Méthodologie et éthique"])
st.sidebar.divider()
st.sidebar.info("100 % local\n\nSans modèle, sans API payante et sans messagerie réelle.")
{"Tableau de bord": dashboard, "Laboratoire": laboratory, "Comparaison": comparison,
 "Historique et journaux": logs, "Méthodologie et éthique": methodology}[page]()
