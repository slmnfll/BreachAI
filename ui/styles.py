"""Identité sobre et composants de présentation du laboratoire."""
import streamlit as st


def header():
    st.html("""<style>
    .block-container {max-width:1320px;padding-top:4.5rem;padding-bottom:3rem;}
    h1,h2,h3 {letter-spacing:-.025em;} h2 {font-size:1.85rem;} h3 {font-size:1.15rem;}
    [data-testid="stMetric"] {background:white;border:1px solid #d8e4eb;border-radius:10px;padding:14px 18px;}
    [data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
    [data-testid="stSidebar"] {border-right:1px solid #d8e4eb;}
    [data-testid="stExpander"] {background:#fff;border-radius:10px;}
    [data-testid="stButton"] button {border-radius:8px;}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size:14px;}
    [data-testid="stAlertContainer"] {border:1px solid color-mix(in srgb, currentColor 35%, transparent);border-radius:10px;}
    [class*="st-key-metric_neutral_"] [data-testid="stMetricValue"] {color:#586774;}
    [class*="st-key-metric_red_"] [data-testid="stMetricValue"] {color:#c33434;}
    [class*="st-key-metric_green_"] [data-testid="stMetricValue"] {color:#22824b;}
    [class*="st-key-metric_yellow_"] [data-testid="stMetricValue"] {color:#a36b00;}
    .st-key-available_scenarios [data-testid="stMetricValue"] {color:#005f85;}
    .lab-bar {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid #ccdce6;padding:0 0 16px;margin:0 0 24px;font-size:13px;}
    .lab-name {font-weight:750;letter-spacing:.06em;color:#005f85;}
    .lab-badge {border:1px solid #bad4df;background:#eaf4f8;border-radius:20px;padding:5px 11px;color:#00516f;}
    .lab-wordmark {font-size:27px;font-weight:800;letter-spacing:-1px;color:#005f85;padding:8px 0 0;}
    .lab-kicker {font-size:12px;font-weight:650;color:#486677;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;}
    @media(max-width:640px){.block-container{padding-left:1rem;padding-right:1rem;} .lab-bar{margin-bottom:16px;} h2{font-size:1.5rem;}}
    </style><div class="lab-bar"><span class="lab-name">BRÈCHIA / ESPACE D’EXPÉRIMENTATION</span><span class="lab-badge">Données synthétiques · Outils fictifs</span></div>""")


def section_title(title, description):
    st.header(title)
    st.caption(description)


def email_card(scenario, identity, title="02 / INSPECTER LE MESSAGE", request=None):
    with st.container(border=True):
        st.caption(title)
        if request:
            st.info(request)
        st.subheader(scenario["subject"])
        st.caption(f"De : {scenario['sender']}  ·  À : {identity.capitalize()}")
        st.divider()
        st.write(scenario["email"])
