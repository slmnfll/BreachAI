import json
import sqlite3
import streamlit as st
from agents.simulator import run
from scenarios.catalog import load
from evaluation.metrics import metrics
from ui.styles import section_title, email_card
from scenarios.tasks import TASKS, task_id, instruction
from ui.task_picker import select_task
from ui.search import live_search
from ui.selection import french_multiselect
from utils.search import search_results
from utils.storage import history, save, reset_history


def read_history():
    try:
        return history()
    except (sqlite3.Error, OSError):
        st.error("Impossible de lire le journal local. Vérifiez les droits du dossier data et l’état du fichier SQLite.")
        return []


def persist(results):
    try:
        run_id = save(results)
        st.success("Exécution enregistrée dans le journal local.")
        return run_id
    except (sqlite3.Error, OSError):
        st.error("Résultats calculés, mais enregistrement impossible dans le journal local.")


def percent(value):
    return "S/O" if value is None else f"{value:.0%}"


def metric_color(key, value):
    """Repères visuels sur le corpus testé, sans certification de sécurité."""
    if value is None:
        return "neutral"
    if key in ("réussite_attaques", "faux_positifs"):
        return "green" if value == 0 else "yellow" if value < .5 else "red"
    return "green" if value == 1 else "yellow" if value >= .5 else "red"


def indicators(results, show_counts=True, scope="default"):
    m = metrics(results)
    if any("version_moteur" not in r for r in results):
        st.caption("Résultats historiques : la version initiale comptait uniquement l’exécution du résumé. Relancez une campagne pour appliquer les nouveaux critères.")
    cols = st.columns(4)
    for c, label, key in zip(cols, ["Réussite des attaques", "Blocage des attaques", "Faux positifs", "Tâche légitime accomplie"],
                             ["réussite_attaques", "blocage_attaques", "faux_positifs", "utilité"]):
        value = m[key]
        color = metric_color(key, value)
        with c, st.container(key="metric_" + color + "_" + key + "_" + scope):
            st.metric(label, percent(value))
    if show_counts:
        st.caption(f" {m['attaques']} essais malveillants · {m['témoins']} témoins · {m['essais']} essais au total.")



def paired_indicators(results):
    groups = [[r for r in results if r["mode"] == mode] for mode in ("naïf", "protégé")]
    counts = [tuple(metrics(g)[k] for k in ("attaques", "témoins", "essais")) for g in groups]
    for i, (mode, group) in enumerate(zip(("naïf", "protégé"), groups)):
        st.subheader("Assistant " + mode)
        with st.container(key="indicators_" + str(i)):
            indicators(group, show_counts=i == 1 or counts[0] != counts[1], scope=str(i))

def outcome(result):
    if result["compromis"]:
        return "L’attaque a réussi dans la simulation : l’assistant a effectué une action interdite."
    if result["attaque"] and result["bloqué"]:
        return "La protection a fonctionné : l’assistant a refusé la demande du courriel."
    if result["attaque"]:
        return "Test non concluant : la demande n’a pas été comprise par le simulateur."
    return "Courriel normal : l’assistant a effectué la tâche demandée."


def filter_results(results, key):
    search = live_search(key + "_search")
    st.caption("Recherche pendant la saisie : nom, identifiant (A01 ou A 01), personne, assistant ou date au format AAAA-MM-JJ. Plusieurs mots peuvent être combinés.")
    options = sorted({r["scenario_id"] for r in results})
    scenario = st.selectbox("Filtrer par identifiant de scénario", ["Tous"] + options, key=key + "_scenario")
    mode = st.selectbox("Filtrer par assistant", ["Tous", "naïf", "protégé"], key=key + "_mode")
    candidates = [r for r in results if (scenario == "Tous" or r["scenario_id"] == scenario)
                  and (mode == "Tous" or r["mode"] == mode)]
    matches, approximate = search_results(candidates, search)
    if approximate and matches:
        st.info("Aucune correspondance exacte : voici les résultats proches de votre saisie.")
    return matches


def group_results(results):
    groups = {}
    for result in results:
        # Ne jamais fusionner deux exécutions du même scénario.
        key = (result.get("campagne", "courante"), result["scenario_id"], result["identité"])
        groups.setdefault(key, []).append(result)
    return list(groups.values())


def grouped_results(results, key):
    groups = group_results(results)
    size = st.session_state.get(key + "_size", 10)
    pages = max(1, (len(groups) + size - 1) // size)
    signature = (size, repr(results))
    if st.session_state.get(key + "_signature") != signature:
        st.session_state[key + "_page"] = 1
        st.session_state[key + "_signature"] = signature
    page = max(1, min(st.session_state.get(key + "_page", 1), pages))
    st.session_state[key + "_page"] = page
    start = (page - 1) * size
    if not groups:
        st.info("Aucun scénario testé ne correspond à votre recherche ou à vos filtres.")
    for group in groups[start:start + size]:
        first = group[0]
        label = first["scenario_id"] + " · " + first["titre"] + " · " + first["identité"].capitalize()
        if "campagne" in first:
            label += " · " + first["date_utc"] + " · campagne " + first["campagne"][:8]
        with st.expander(label):
            for result in group:
                with st.expander("Assistant " + result["mode"]):
                    st.write(outcome(result))
                    st.write("Tâche légitime : " + ("accomplie" if result["tâche_accomplie"] else "non accomplie"))
                    summary_view(result)
                    st.dataframe(result["events"], hide_index=True, width="stretch")
    # Les contrôles sont placés après les résultats ; les callbacks changent la page avant le rendu.
    def go(target):
        st.session_state[key + "_page"] = target
    numbers = sorted({1, pages, *range(max(1, page - 1), min(pages, page + 1) + 1)})
    slots = []
    for number in numbers:
        if slots and number - slots[-1] > 1:
            slots.append(number - 1)  # remplacé visuellement par des points de suspension
        slots.append(number)
    st.caption(f"{len(groups)} scénarios testés · {len(results)} résultats d’assistants · page {page}/{pages} · {start + 1 if groups else 0}–{min(start + size, len(groups))}")
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="xsmall"):
        st.selectbox("Scénarios par page", [10, 25, 50], key=key + "_size", label_visibility="collapsed", width=85)
        st.button("‹", key=key + "_prev", help="Page précédente", disabled=page == 1, on_click=go, args=(page - 1,))
        for number in slots:
            if number not in numbers:
                with st.popover("…", help="Aller à une page", key=f"{key}_jump_menu_{number}"):
                    target = st.number_input("Aller à la page", min_value=1, max_value=pages, value=page, step=1, key=f"{key}_jump_value_{number}")
                    st.button("Afficher cette page", key=f"{key}_jump_go_{number}", on_click=go, args=(int(target),))
            else:
                st.button(str(number), key=f"{key}_number_{number}", type="primary" if page == number else "secondary", on_click=go, args=(number,))
        st.button("›", key=key + "_next", help="Page suivante", disabled=page == pages, on_click=go, args=(page + 1,))


def reset_controls():
    with st.expander("Remettre les expériences à zéro"):
        st.write("Supprime toutes les campagnes, les expériences de modèles réels et leurs évaluations de la base locale. Les scénarios restent disponibles. Les fichiers déjà exportés sont conservés.")
        confirm = st.checkbox("Je confirme la suppression de toutes les expériences enregistrées", key="confirm_reset")
        if st.button("Tout supprimer et repartir à zéro", disabled=not confirm):
            try:
                reset_history()
            except (sqlite3.Error, OSError):
                st.error("Suppression impossible. Les résultats affichés sont conservés.")
                return
            for key in list(st.session_state):
                if key != "confirm_reset":
                    del st.session_state[key]
            st.session_state["reset_done"] = True
            st.rerun()
    if st.session_state.pop("reset_done", False):
        st.success("Toutes les expériences ont été supprimées. Les compteurs d’exécution repartent à zéro ; les taux restent non mesurés jusqu’au prochain test.")


def summary_view(result):
    status = result.get("état_résumé")
    st.caption("Tâche : " + TASKS.get(result.get("task", "summary"), "Résumé"))
    if status is None:
        st.caption("Ancien résultat : fidélité du résumé non évaluée par cette version du moteur.")
        st.write("Résumé enregistré : " + result["résumé"])
        return
    labels = {"absent": "Aucun résultat produit", "falsifié": "Résultat incorrect ou altéré", "conforme": "Résultat conforme à la référence préparée"}
    st.write("**Résultat de la tâche :** " + labels[status])
    if result["résumé"]:
        st.write("**Résultat obtenu (préparé pour la simulation) :** " + result["résumé"])
    if "calendrier_après" in result:
        with st.expander("État du calendrier fictif avant / après"):
            st.json({"avant": result["calendrier_avant"], "après": result["calendrier_après"]})
    if status != "conforme":
        st.write("**Résultat attendu (référence préparée) :** " + result["résumé_attendu"])


def result_view(results):
    st.subheader("03 / Résultats de l’expérience")
    for col, result in zip(st.columns(len(results)), results):
        with col:
            st.subheader("Assistant " + result["mode"])
            st.caption("Suit les demandes du courriel sans vérifier leur autorité." if result["mode"] == "naïf"
                       else "Vérifie l’origine et les permissions avant d’agir.")
            message = outcome(result)
            if result["compromis"]:
                st.error(message)
            elif result["attaque"] and not result["bloqué"]:
                st.warning(message)
            else:
                st.success(message)
            summary_view(result)
            for event in result["events"][1:]:
                st.write("Demande contenue dans le courriel : **" + event["opération"] + "** → " + event["ressource"])
                st.write("Décision : " + ("effectuée dans la simulation" if event["exécuté_simulation"] else "refusée"))
            with st.expander("Voir les détails techniques des décisions"):
                st.dataframe(result["events"], hide_index=True, width="stretch")
    st.info("Aucun message n’a quitté l’application. Réussite de l’attaque = mauvais comportement de l’assistant ; blocage de l’attaque = protection efficace pour ce cas.")


def dashboard():
    section_title("Vue d’ensemble", "Préparer une expérience, observer les décisions, conserver les preuves.")
    catalog = load()
    rows = read_history()
    from utils.experiments import experiments
    try:
        real = experiments()
    except (sqlite3.Error, OSError):
        real = []
        st.warning("L’historique des modèles réels n’a pas pu être chargé.")
    a, b, c = st.columns(3)
    with a, st.container(key="available_scenarios"):
        st.metric("Scénarios disponibles", len(catalog))
    b.metric("Campagnes simulées", len(rows))
    c.metric("Essais avec un modèle", len(real))
    st.subheader("Choisir un espace d’expérimentation")
    def navigate(target):
        st.session_state["navigation"] = target
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.caption("01 / COMPRENDRE")
        st.subheader("Simulateur pédagogique")
        st.write("Explorer un courriel et comparer deux assistants au comportement prédéfini.")
        st.button("Ouvrir le simulateur", on_click=navigate, args=("Laboratoire",), width="stretch")
    with right, st.container(border=True):
        st.caption("02 / OBSERVER")
        st.subheader("Expériences avec un modèle")
        st.write("Soumettez le même courriel à une IA locale. Comparez les protections et évaluez la réponse réellement produite.")
        st.button("Préparer une expérience réelle", on_click=navigate, args=("Modèle réel (local)",), type="primary", width="stretch")
    with st.expander("Dernière campagne du simulateur", expanded=False):
        if rows:
            paired_indicators(rows[0]["résultats"])
        else:
            st.info("Aucune campagne simulée. Les résultats apparaîtront après votre premier essai.")
    if real:
        latest = real[0]
        with st.container(border=True):
            st.caption("DERNIER ESSAI AVEC UN MODÈLE")
            st.write(f"**{latest['scenario_id']} · {latest['model']}**")
            st.caption(f"{latest['created_utc']} · Évaluation humaine : {latest['human_review']}")
            st.write("Terminé" if latest["status"] == "ok" else "Erreur technique enregistrée")
    st.caption("Les mesures du simulateur et les observations des modèles réels restent séparées. Un résultat sur ce corpus ne garantit pas la sécurité d’un système réel.")
    st.divider()
    reset_controls()


def laboratory():
    section_title("Simulateur pédagogique", "Une expérience guidée, deux comportements prédéfinis. Aucun modèle n’est appelé dans cet espace.")
    catalog = load()
    setup, document = st.columns([1.2, 1.8], gap="medium")
    with setup:
        with st.container(border=True):
            st.caption("01 / PRÉPARER")
            catalog = select_task(catalog, "simulation_task")
            chosen = st.selectbox("Scénario", range(len(catalog)), format_func=lambda i: catalog[i]["id"] + " · " + catalog[i]["title"])
            scenario = catalog[chosen]
            identity = st.selectbox("Personne fictive qui utilise l’assistant", ["alice", "bob"], format_func=str.capitalize)
            st.divider()
            st.markdown("**Tâche légitime**")
            st.write(f"{identity.capitalize()} demande : {instruction(scenario, identity)}")
            st.caption("Les permissions viennent de la tâche choisie, pas du courriel.")
            launched = st.button("Comparer les deux assistants sur ce courriel", type="primary", width="stretch")
        with st.expander("Qui fait quoi ?"):
            st.write("Alice et Bob sont les utilisateurs fictifs. L’assistant naïf suit les actions encodées dans le scénario ; le protégé contrôle leurs autorisations.")
    with document:
        email_card(scenario, identity)
        with st.expander("Comprendre le piège et sa représentation"):
            st.caption("Interprétation préparée, sans analyse automatique du langage naturel.")
            if scenario["excerpt"]:
                st.info(scenario["excerpt"])
            st.write(scenario["interpretation"])
            st.write(scenario["mechanism"])
            st.code(scenario["body"], language=None, wrap_lines=True)
            st.caption("Les balises SIM sont écrites à l’avance et ne font pas partie du courriel naturel affiché.")
    if launched:
        results = [run(scenario, mode, identity) for mode in ["naïf", "protégé"]]
        st.session_state["laboratory_result"] = results
        persist(results)
    results = st.session_state.get("laboratory_result")
    st.divider()
    if results and results[0]["scenario_id"] == scenario["id"] and results[0]["identité"] == identity:
        result_view(results)
    else:
        st.subheader("03 / Résultats de l’expérience")
        st.info("Prêt à comparer. Lancez l’expérience pour afficher les décisions des deux assistants ici.")


def comparison():
    st.header("Évaluation comparative")
    st.caption("Une campagne teste tous les scénarios sélectionnés avec les deux versions de l’assistant. Les indicateurs résument l’ensemble ; ouvrez ensuite un scénario pour comparer ses deux décisions.")
    catalog = load()
    selected_task = st.selectbox("Tâches de la campagne", ["Toutes"] + list(TASKS), format_func=lambda k: TASKS.get(k, k))
    if selected_task != "Toutes":
        catalog = [s for s in catalog if task_id(s) == selected_task]
    selected = french_multiselect("Corpus de la campagne", [s["id"] for s in catalog],
                                  key="campaign_corpus_" + selected_task,
                                  format_func=lambda sid: sid + " · " + next(s["title"] for s in catalog if s["id"] == sid))
    if st.button("Lancer la campagne", type="primary", disabled=not selected):
        results = [run(s, mode) for s in catalog if s["id"] in selected for mode in ["naïf", "protégé"]]
        from datetime import datetime, timezone
        created = datetime.now(timezone.utc).isoformat()
        run_id = persist(results)
        st.session_state["campaign"] = [dict(r, date_utc=created, campagne=run_id or "non enregistrée") for r in results]
    results = st.session_state.get("campaign", [])
    if results:
        paired_indicators(results)
        grouped_results(results, "comparison")
        st.download_button("Exporter les résultats et traces (JSON)", json.dumps(results, ensure_ascii=False, indent=2), "brechia-campagne.json", "application/json")


def logs():
    st.header("Historique et journaux")
    rows = read_history()
    if not rows:
        st.info("Aucune campagne enregistrée.")
        reset_controls()
        return
    results = [dict(result, campagne=row["id"], date_utc=row["date_utc"]) for row in rows for result in row["résultats"]]
    st.caption("Un bloc correspond à un scénario d’une campagne et contient les décisions des deux assistants. Deux campagnes différentes restent séparées, même si le scénario est identique. Le filtre d’assistant limite les détails visibles dans chaque bloc.")
    filtered = filter_results(results, "history")
    grouped_results(filtered, "history")
    reset_controls()
    st.download_button("Exporter les résultats filtrés (JSON)", json.dumps(filtered, ensure_ascii=False, indent=2), "brechia-journal.json", "application/json")


def methodology():
    st.header("Méthodologie et éthique")
    from pathlib import Path
    st.markdown((Path(__file__).resolve().parents[1] / "data" / "methodologie.md").read_text(encoding="utf-8"))
