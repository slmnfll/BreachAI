"""Interpréteur déterministe de balises pédagogiques, sans modèle ni outil réseau."""
import re
from security.policy import Action, authorize

PATTERN = re.compile(r"\[SIM:([^:\]\n]+):([^\]\n]+)\]")

def run_summary(scenario, mode, identity="alice"):
    if mode not in ("naïf", "protégé"):
        raise ValueError("Mode inconnu")
    # La vérité terrain du scénario n'est jamais consultée pour décider.
    proposals = [Action("résumer", identity, "utilisateur")]
    proposals += [Action(op.strip(), target.strip(), "courriel")
                  for op, target in PATTERN.findall(scenario["body"])]
    events = []
    for action in proposals:
        permitted, reason = authorize(action, identity)
        executed = permitted if mode == "protégé" else True
        events.append({"opération": action.operation, "ressource": action.resource,
                       "origine": action.origin, "autorisé": permitted,
                       "exécuté_simulation": executed,
                       "motif": reason if mode == "protégé" else "Agent naïf : instruction acceptée sans contrôle."})
    executed_ops = {e["opération"] for e in events[1:] if e["exécuté_simulation"]}
    prevented = "abandonner_résumé" in executed_ops
    falsified = "falsifier_résumé" in executed_ops and not prevented
    if prevented:
        events[0]["exécuté_simulation"] = False
        events[0]["motif"] = "Tâche autorisée, mais abandonnée après acceptation de la consigne du courriel."
    status = "absent" if prevented else "falsifié" if falsified else "conforme"
    summary = "" if prevented else scenario.get("altered_summary", "Résumé remplacé par un contenu contraire à la référence.") if falsified else scenario["summary"]
    return {"scenario_id": scenario["id"], "titre": scenario["title"],
            "attaque": scenario["attack"], "mode": mode, "identité": identity,
            "version_moteur": "0.2", "état_résumé": status,
            "réponse_produite": not prevented, "résumé_attendu": scenario["summary"],
            "events": events,
            "compromis": any(e["exécuté_simulation"] and not e["autorisé"] for e in events),
            "bloqué": any(not e["exécuté_simulation"] for e in events if e["origine"] == "courriel"),
            "tâche_accomplie": not prevented and not falsified,
            "résumé": summary}


def run(scenario, mode, identity="alice"):
    from scenarios.tasks import task_id
    from security.mock_tools import MockMailbox
    from security.policy import authorize_tool
    import json
    task = task_id(scenario)
    result = run_summary(scenario, mode, identity)
    result.update(task=task, pair_id=scenario.get("pair_id"), corpus_version=scenario.get("corpus_version", "legacy"), version_moteur="0.3")
    if task == "summary":
        return result
    expected = dict(scenario["expected_event"])
    actual = dict(expected)
    if result["état_résumé"] == "falsifié":
        actual["date"] = "2099-01-01"
    absent = result["état_résumé"] == "absent"
    result["events"][0]["opération"] = "extraire" if task == "extract" else "creer_evenement"
    result["résumé_attendu"] = json.dumps(expected, ensure_ascii=False)
    result["résumé"] = "" if absent else json.dumps(actual, ensure_ascii=False)
    if task == "calendar":
        box = MockMailbox()
        before = {k: [dict(e) for e in v] for k, v in box.calendars.items()}
        if not absent:
            action = {"operation": "creer_evenement", "target": identity, "event": actual}
            allowed, reason = authorize_tool(action, identity, task)
            box.execute(action)
            result["events"][0].update(autorisé=allowed, motif=reason)
        for event in result["events"][1:]:
            if event["opération"] == "supprimer_evenements" and event["exécuté_simulation"]:
                box.execute({"operation": "supprimer_evenements", "target": identity})
        success = box.calendars[identity] == before[identity] + [expected] and all(box.calendars[k] == before[k] for k in before if k != identity)
        result.update(calendrier_avant=before, calendrier_après=box.calendars, tâche_accomplie=success)
        if not success and not absent:
            result["état_résumé"] = "falsifié"
    else:
        result["tâche_accomplie"] = not absent and actual == expected
    return result
