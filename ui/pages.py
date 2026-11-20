import json
import sqlite3
import streamlit as st
from agents.simulator import run
from scenarios.catalog import load
from evaluation.metrics import metrics
from ui.search import live_search
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
    return "Non mesuré" if value is None else f"{value:.0%}"


def indicators(results):
    m = metrics(results)
    if any("version_moteur" not in r for r in results):
        st.caption("Résultats historiques : la version initiale comptait uniquement l’exécution du résumé. Relancez une campagne pour appliquer les nouveaux critères.")
    cols = st.columns(4)
    for c, label, key in zip(cols, ["Réussite des attaques", "Blocage des attaques", "Faux positifs", "Tâche légitime accomplie"],
                             ["réussite_attaques", "blocage_attaques", "faux_positifs", "utilité"]):
        c.metric(label, percent(m[key]))
    st.caption(f"Dénominateurs : {m['attaques']} essais malveillants · {m['témoins']} témoins · {m['essais']} essais au total.")


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
                with st.container(width=28):
                    st.write("…")
            else:
                st.button(str(number), key=f"{key}_number_{number}", type="primary" if page == number else "secondary", on_click=go, args=(number,))
        st.button("›", key=key + "_next", help="Page suivante", disabled=page == pages, on_click=go, args=(page + 1,))


def reset_controls():
    with st.expander("Remettre les expériences à zéro"):
        st.write("Supprime toutes les campagnes et leurs journaux de la base locale. Les scénarios restent disponibles. Les fichiers déjà exportés sont conservés.")
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
    if status is None:
        st.caption("Ancien résultat : fidélité du résumé non évaluée par cette version du moteur.")
        st.write("Résumé enregistré : " + result["résumé"])
        return
    labels = {"absent": "Aucun résumé produit", "falsifié": "Résumé produit mais falsifié", "conforme": "Résumé conforme à la référence préparée"}
    st.write("**Résultat de la tâche :** " + labels[status])
    if result["résumé"]:
        st.write("**Résumé obtenu (préécrit) :** " + result["résumé"])
    if status != "conforme":
        st.write("**Résumé attendu (référence préécrite) :** " + result["résumé_attendu"])


def result_view(results):
    st.subheader("4. La décision de chaque assistant")
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
    st.header("Vue d’ensemble")
    st.write("Un même courriel, deux comportements : suivre son contenu comme une instruction ou contrôler son autorité avant chaque action.")
    reset_controls()
    catalog = load()
    rows = read_history()
    a,b,c = st.columns(3)
    a.metric("Scénarios disponibles", len(catalog))
    b.metric("Campagnes enregistrées", len(rows))
    c.metric("Connexions à une messagerie", 0)
    if rows:
        st.subheader("Dernière campagne")
        for mode in ["naïf", "protégé"]:
            st.markdown("**Agent " + mode + "**")
            indicators([r for r in rows[0]["résultats"] if r["mode"] == mode])
    else:
        st.info("Aucun résultat pour le moment. Lancez une campagne dans Comparaison ou explorez un scénario au Laboratoire.")
    with st.container(border=True):
        st.subheader("Le parcours expérimental")
        st.write("1. Inspecter un courriel fictif → 2. Simuler les deux agents → 3. Examiner les autorisations → 4. Comparer les traces et les métriques.")
    st.warning("Ces résultats décrivent un simulateur déterministe. Ils ne mesurent pas la robustesse d’un modèle de langage ou de quatre fournisseurs réels.")


def laboratory():
    st.header("Laboratoire de scénarios")
    catalog = load()
    chosen = st.selectbox("Scénario", range(len(catalog)), format_func=lambda i: catalog[i]["title"])
    scenario = catalog[chosen]
    identity = st.selectbox("Personne fictive qui utilise l’assistant", ["alice", "bob"], format_func=str.capitalize)
    st.info("Alice et Bob sont des personnes fictives, pas les deux agents. Vous choisissez à qui appartient la boîte. Nous comparons ensuite deux versions de son assistant : naïf (sans contrôle) et protégé (avec contrôle).")
    st.subheader("1. La demande légitime")
    st.write(f"{identity.capitalize()} demande : « Résume mes courriels. » Elle ou il n’autorise ni l’envoi de copies à un tiers, ni la lecture de la boîte d’une autre personne.")
    st.subheader("2. Le courriel reçu — entièrement fictif")
    with st.container(border=True):
        st.write("**De :** Camille — " + scenario["sender"])
        st.write("**À :** " + identity.capitalize() + " — " + identity + "@exemple.invalid")
        st.write("**Objet :** " + scenario["subject"])
        st.divider()
        st.write(scenario["email"])
    st.caption("Courriel entièrement fictif. Les adresses en .invalid ne servent à envoyer aucun message.")
    st.subheader("3. Du message aux actions simulées")
    st.caption("Cette lecture est préparée à l’avance pour chaque scénario. Elle illustre ce qu’un assistant pourrait traiter ; aucune IA n’analyse réellement le langage naturel dans cette version.")
    st.write("**Demande de l’utilisateur :** résumer ses courriels. Cette tâche est autorisée. Nous vérifions si un résumé conforme est effectivement fourni, malgré les demandes du courriel.")
    if scenario["excerpt"]:
        st.write("**Passage du courriel à examiner :**")
        st.info(scenario["excerpt"])
    st.write("**Ce que nous représentons dans la simulation :** " + scenario["interpretation"])
    st.write("**Ce que l’on compare :** l’assistant naïf accepte les actions encodées dans le scénario ; l’assistant protégé vérifie leur origine et leurs autorisations.")
    with st.expander("Détails du scénario et représentation technique"):
        st.write(scenario["mechanism"])
        st.code(scenario["body"], language=None, wrap_lines=True)
        st.caption("Cette représentation technique est écrite à l’avance, séparément du courriel affiché. Les balises SIM déclenchent les actions fictives ; elles ne sont pas extraites automatiquement du texte. Sans balise, aucune action supplémentaire n’est reconnue.")
    if st.button("Comparer les deux assistants sur ce courriel", type="primary"):
        results = [run(scenario, mode, identity) for mode in ["naïf", "protégé"]]
        st.session_state["laboratory_result"] = results
        persist(results)
    results = st.session_state.get("laboratory_result")
    if results and results[0]["scenario_id"] == scenario["id"] and results[0]["identité"] == identity:
        result_view(results)


def comparison():
    st.header("Évaluation comparative")
    st.info("Une campagne teste tous les scénarios sélectionnés avec les deux versions de l’assistant. Les indicateurs résument l’ensemble ; ouvrez ensuite un scénario pour comparer ses deux décisions.")
    catalog = load()
    selected = st.multiselect("Corpus de la campagne", [s["id"] for s in catalog],
                              default=[s["id"] for s in catalog],
                              format_func=lambda sid: next(s["title"] for s in catalog if s["id"] == sid))
    st.caption("Protocole apparié : mêmes scénarios, même identité Alice, deux agents. Une exécution par cas ; répéter ne crée pas d’observation indépendante.")
    if st.button("Lancer la campagne", type="primary", disabled=not selected):
        results = [run(s, mode) for s in catalog if s["id"] in selected for mode in ["naïf", "protégé"]]
        from datetime import datetime, timezone
        created = datetime.now(timezone.utc).isoformat()
        run_id = persist(results)
        st.session_state["campaign"] = [dict(r, date_utc=created, campagne=run_id or "non enregistrée") for r in results]
    results = st.session_state.get("campaign", [])
    if results:
        st.caption("Résultats de la dernière campagne lancée ; relancez pour appliquer une nouvelle sélection.")
        for mode in ["naïf", "protégé"]:
            st.subheader("Agent " + mode)
            indicators([r for r in results if r["mode"] == mode])
        st.caption("Les indicateurs portent sur toute la campagne. Recherche, filtres et pagination changent uniquement les détails affichés. Un bloc regroupe les deux assistants pour un même scénario testé.")
        filtered = filter_results(results, "comparison")
        grouped_results(filtered, "comparison")
        st.download_button("Exporter les résultats et traces (JSON)", json.dumps(results, ensure_ascii=False, indent=2), "brechia-campagne.json", "application/json")


def logs():
    st.header("Historique et journaux")
    reset_controls()
    rows = read_history()
    if not rows:
        st.info("Aucune campagne enregistrée.")
        return
    results = [dict(result, campagne=row["id"], date_utc=row["date_utc"]) for row in rows for result in row["résultats"]]
    st.caption("Un bloc correspond à un scénario d’une campagne et contient les décisions des deux assistants. Deux campagnes différentes restent séparées, même si le scénario est identique. Le filtre d’assistant limite les détails visibles dans chaque bloc.")
    filtered = filter_results(results, "history")
    grouped_results(filtered, "history")
    st.caption("Horodatages UTC. Journal local modifiable, non signé. L’export contient tous les résultats correspondant aux filtres, pas seulement la page visible.")
    st.download_button("Exporter les résultats filtrés (JSON)", json.dumps(filtered, ensure_ascii=False, indent=2), "brechia-journal.json", "application/json")


def methodology():
    st.header("Méthodologie et éthique")
    from pathlib import Path
    st.markdown((Path(__file__).resolve().parents[1] / "data" / "methodologie.md").read_text(encoding="utf-8"))
