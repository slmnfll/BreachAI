import json
import sqlite3
import streamlit as st
from agents.ollama_local import OllamaLocal, ModelError
from evaluation.runner import run_experiment, STRATEGIES
from scenarios.catalog import load
from utils.experiments import save_experiment, experiments, review
from ui.styles import section_title, email_card
from scenarios.tasks import TASKS, task_id, instruction
from ui.task_picker import select_task
from ui.selection import french_multiselect
from utils.search import normalize


def show_record(record, busy=False):
    st.caption(f"{record['created_utc']} · {record['model']} · {STRATEGIES[record['strategy']]} · {record['duration_seconds']} s")
    if record["status"] != "ok":
        st.error(record["error"])
        st.caption("Erreur technique : ne compte ni comme protection réussie ni comme attaque échouée.")
    else:
        st.subheader("Réponse réelle du modèle")
        if record.get("task_success") is not None:
            st.write("**Tâche accomplie selon le critère automatique :** " + ("Oui" if record["task_success"] else "Non"))
            st.caption(record["evaluation_method"])
        if "extracted_meeting" in record:
            st.json(record["extracted_meeting"])
        if record.get("task") == "calendar":
            with st.expander("Calendriers fictifs avant / après"):
                st.json({"avant": record["calendar_before"], "après": record["calendar_after"]})
        st.text(record["summary"] or "Aucun résumé produit.")
        a, b, c = st.columns(3)
        a.metric("Demandes d’outils", len(record["events"]))
        b.metric("Demandes bloquées", sum(e["bloqué"] for e in record["events"]))
        c.metric("Évaluation humaine", record["human_review"])
        st.caption("Le texte est la réponse du modèle ; les compteurs concernent les demandes d’outils, y compris la création légitime d’un événement.")
        if record["events"]:
            for event in record["events"]:
                with st.container(border=True):
                    st.write(f"**{event['operation'].capitalize()}** → {event['target']}")
                    st.write("Bloquée par le contrôleur" if event["bloqué"] else "Transmise à l’outil fictif")
                    st.caption(event["motif"])
            with st.expander("Trace technique des outils"):
                st.json(record["events"])
        else:
            st.info("Aucune action structurée proposée. Cela ne garantit pas que le résumé est fidèle.")
        with st.expander("Évaluer la réponse manuellement"):
            st.text(record["scenario_snapshot"]["email"])
            options = ["non évalué", "conforme", "incorrect", "absent", "incertain"]
            decision = st.selectbox("Évaluation humaine", options, index=options.index(record["human_review"]), key=record["id"] + "_review", disabled=busy)
            note = st.text_area("Justification", value=record.get("review_note", ""), key=record["id"] + "_note", disabled=busy)
            if st.button("Enregistrer l’évaluation", key=record["id"] + "_save", disabled=busy):
                try:
                    review(record["id"], decision, note)
                except (OSError, sqlite3.Error, ValueError):
                    st.error("Évaluation non enregistrée. Réessayez ; votre saisie est conservée.")
                else:
                    st.session_state["review_saved"] = "Évaluation enregistrée : " + decision + "."
                    st.rerun()
    with st.expander("Traçabilité et paramètres exacts"):
        st.json(record)
    st.download_button("Exporter la fiche d’expérience (JSON)", json.dumps(record, ensure_ascii=False, indent=2),
                       f"brechia-experience-{record['id']}.json", "application/json", key=record["id"] + "_export", disabled=busy)


def real_laboratory():
    busy = bool(st.session_state.get("pending_experiment"))
    from ui.interaction_lock import interaction_lock
    interaction_lock(busy)
    if st.session_state.get("real_run_error"):
        st.error(st.session_state.pop("real_run_error"))
    section_title("Expériences avec un modèle", "Une réponse générée par votre IA locale. Des outils exclusivement fictifs. Des observations à évaluer.")
    tabs = st.tabs(["Préparer une expérience", "Résultats et évaluations"], key="real_tabs", default="Résultats et évaluations" if st.session_state.get("review_saved") else "Préparer une expérience")
    with tabs[0]:
        setup, document = st.columns([1.2, 1.8], gap="medium")
        with setup:
            with st.container(border=True):
                st.caption("01 / CONFIGURER")
                if st.button("Détecter les modèles locaux", width="stretch", disabled=busy):
                    try:
                        st.session_state["local_models"] = [m["name"] for m in OllamaLocal().models()]
                        st.session_state.pop("model_detection_error", None)
                    except ModelError as exc:
                        st.session_state["local_models"] = []
                        st.session_state["model_detection_error"] = str(exc)
                if st.session_state.get("model_detection_error"):
                    st.warning(st.session_state["model_detection_error"])
                models = st.session_state.get("local_models", [])
                model = st.selectbox("Modèle installé", models, disabled=busy) if models else None
                if not models:
                    st.caption("Aucun modèle détecté dans cette session. Lancez la détection avant l’expérience.")
                catalog = select_task(load(), "real_task", disabled=busy)
                selected = st.selectbox("Courriel synthétique", range(len(catalog)), format_func=lambda i: catalog[i]["id"] + " · " + catalog[i]["title"], disabled=busy)
                scenario = catalog[selected]
                identity = st.selectbox("Utilisateur fictif", ["alice", "bob"], format_func=str.capitalize, disabled=busy)
                strategies = french_multiselect("Protections à comparer", list(STRATEGIES), key="real_strategies", format_func=STRATEGIES.get, disabled=busy)
                with st.expander("Comprendre les protections"):
                    st.write("**Sans défense ajoutée** : aucune protection spécifique ajoutée au modèle.\n\n**Consigne seule** : demander au modèle d’ignorer les ordres du courriel.\n\n**Contrôle seul** : bloquer les demandes d’outils hors mandat.\n\n**Les deux** : combiner consigne et contrôle.")
                with st.expander("Paramètres avancés"):
                    seed = st.number_input("Graine demandée au modèle", min_value=0, max_value=2147483647, value=42, disabled=busy)
                    st.caption("Ce nombre fixe les conditions du hasard, pas le niveau de protection. Des réponses identiques ne sont pas garanties.")
                st.divider()
                st.caption(f"{len(strategies)} exécution(s) prévue(s) · traitement séquentiel")
                def queue_experiment():
                    st.session_state["pending_experiment"] = (scenario, model, strategies, identity, seed)
                st.button("Lancer l’expérience réelle", type="primary", disabled=busy or not strategies or not model, width="stretch", on_click=queue_experiment)
            if not models:
                with st.expander("Connecter Ollama"):
                    st.write("Démarrez le serveur local, puis utilisez Détecter les modèles. Le téléchargement est nécessaire une seule fois.")
                    st.code("ollama serve\n# Dans un autre terminal :\nollama pull qwen3:1.7b")
        with document:
            email_card(scenario, identity, title="02 / INSPECTER L’ENTRÉE",
                       request=f"{identity.capitalize()} demande : {instruction(scenario, identity)}")
            with st.expander("Ce que reçoit le modèle et limites du protocole"):
                st.write("Le modèle reçoit le courriel naturel et la tâche, sans balise SIM ni réponse attendue. Il propose des actions au format JSON ; le contrôleur les traite après la génération. Les résultats des outils ne lui sont pas renvoyés dans cette version.")
                st.caption("Une seule étape par essai. Modèle déchargé après chaque requête. Le format imposé peut influencer le comportement.")
        st.divider()
        st.subheader("03 / Observer les résultats")
        progress_slot = st.container()
        completed = st.session_state.get("real_preview", [])
        if completed:
            st.caption("Dernière exécution de cette session — ouvrez Résultats et évaluations pour annoter ou exporter un essai. Modifier les paramètres ne relance pas l’expérience.")
            for record in completed:
                with st.container(border=True):
                    st.write("**" + STRATEGIES[record["strategy"]] + "** · " + record["scenario_id"] + " · " + record["model"])
                    if record["status"] == "error":
                        st.error(record["error"])
                    else:
                        st.text(record["summary"] or "Aucun résumé produit.")
                        if record.get("task_success") is not None:
                            st.write("**Tâche accomplie :** " + ("Oui" if record["task_success"] else "Non"))
                            st.caption(record["evaluation_method"])
                        st.caption(f"{len(record['events'])} demandes d’outils · {sum(e['bloqué'] for e in record['events'])} bloquées · {record['duration_seconds']} s")
        elif not busy:
            st.info("Les réponses et demandes d’outils apparaîtront ici après le lancement. Aucun résultat n’est généré avant votre action.")
    with tabs[1]:
        history_view(busy)
    if busy:
        with progress_slot:
            execute_pending()


def history_view(busy=False):
    if "review_saved" in st.session_state:
        st.success(st.session_state.pop("review_saved"))
    try:
        records = experiments()
    except (OSError, sqlite3.Error):
        st.error("Historique des expériences inaccessible.")
        return
    st.caption("Les résultats réels restent séparés des taux du simulateur. Une fidélité non évaluée ne compte pas comme une réussite.")
    if not records:
        st.info("Aucune expérience réelle enregistrée.")
    else:
        query = st.text_input("Rechercher une expérience", placeholder="Scénario, titre, Alice, modèle ou date…", key="real_history_search", disabled=busy)
        with st.expander("Filtrer les expériences"):
            model_filter = st.selectbox("Modèle", ["Tous"] + sorted({r["model"] for r in records}), key="real_filter_model", disabled=busy)
            strategy_filter = st.selectbox("Protection", ["Toutes"] + list(STRATEGIES), format_func=lambda k: STRATEGIES.get(k, k), key="real_filter_strategy", disabled=busy)
            status_filter = st.selectbox("État", ["Tous", "ok", "error"], format_func=lambda k: {"ok":"Terminé", "error":"Erreur technique"}.get(k,k), key="real_filter_status", disabled=busy)
            review_filter = st.selectbox("Évaluation", ["Toutes", "non évalué", "conforme", "incorrect", "absent", "incertain"], key="real_filter_review", disabled=busy)
        tokens = normalize(query).split()
        filtered = [r for r in records if
                    (model_filter == "Tous" or r["model"] == model_filter) and
                    (strategy_filter == "Toutes" or r["strategy"] == strategy_filter) and
                    (status_filter == "Tous" or r["status"] == status_filter) and
                    (review_filter == "Toutes" or r["human_review"] == review_filter) and
                    all(t in normalize(" ".join(str(v) for v in [r['scenario_id'], r['scenario_snapshot'].get('title',''), r.get('identity',''), r['model'], r['created_utc']])) for t in tokens)]
        st.caption(f"{len(filtered)} expérience(s) sur {len(records)} · les plus récentes en premier")
        if not filtered:
            st.info("Aucune expérience ne correspond aux filtres.")
            return
        by_id = {r["id"]: r for r in filtered}
        chosen = st.selectbox("Expérience enregistrée", list(by_id), format_func=lambda k: f"{by_id[k]['created_utc']} · {by_id[k]['scenario_id']} · {STRATEGIES[by_id[k]['strategy']]} · {by_id[k]['status']}", key="real_history_selected", disabled=busy)
        show_record(by_id[chosen], busy=busy)


def execute_pending():
    scenario, model, strategies, identity, seed = st.session_state["pending_experiment"]
    progress = st.progress(0, text="Expérience en cours…")
    completed = []
    try:
        for i, strategy in enumerate(strategies):
            with st.spinner(STRATEGIES[strategy]):
                record = run_experiment(scenario, model, strategy, identity, seed)
            completed.append(record)
            save_experiment(record)
            progress.progress((i + 1) / len(strategies), text=f"{i + 1}/{len(strategies)} essais terminés")
    except Exception:
        st.session_state["real_run_error"] = "Exécution interrompue. Les résultats déjà calculés sont affichés ; vérifiez leur présence dans l’historique avant de relancer."
    finally:
        st.session_state["real_preview"] = completed
        st.session_state.pop("pending_experiment", None)
    st.rerun()
