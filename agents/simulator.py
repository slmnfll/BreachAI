"""Interpréteur déterministe de balises pédagogiques, sans modèle ni outil réseau."""
import re
from security.policy import Action, authorize

PATTERN = re.compile(r"\[SIM:([^:\]\n]+):([^\]\n]+)\]")

def run(scenario, mode, identity="alice"):
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
