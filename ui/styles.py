import streamlit as st

def header():
    st.html("""<style>
    .block-container {max-width:1180px;padding-top:2rem;}
    h1,h2,h3 {letter-spacing:-.025em;}
    [data-testid="stMetric"] {background:white;border:1px solid #d8e4eb;border-radius:14px;padding:16px;}
    .hero {background:#005f85;color:white;padding:30px;border-radius:20px;margin-bottom:24px;}
    .hero h1 {color:white;margin:0;} .hero p {color:#e1f0f6;margin:6px 0;}
    </style><div class="hero"><p>INF5163 · LABORATOIRE LOCAL · VERSION 0.1</p>
    <h1>BrèchIA</h1><p>Comprendre l’injection indirecte. Observer les décisions. Évaluer les protections.</p></div>""")
    st.caption("Simulation pédagogique indépendante • Données fictives • Aucun fournisseur testé • Aucune affiliation officielle à l’UQO")
