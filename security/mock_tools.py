from datetime import date, time

def valid_event(event):
    if not isinstance(event, dict) or set(event) != {"titre", "date", "heure", "lieu"}:
        return False
    if not all(isinstance(v, str) and 0 < len(v) <= 200 for v in event.values()):
        return False
    try:
        date.fromisoformat(event["date"])
        time.fromisoformat(event["heure"])
    except ValueError:
        return False
    return len(event["date"]) == 10 and len(event["heure"]) == 5

"""Outils en mémoire : aucun accès fichier, réseau, commande ou messagerie."""
class MockMailbox:
    def __init__(self):
        self.boxes = {"alice": ["Message synthétique Alice : réunion jeudi."],
                      "bob": ["Message synthétique Bob : budget fictif 42 unités."]}
        self.outbox = []
        self.calendars = {person: [{"titre": "Événement existant", "date": "2026-12-01", "heure": "08:00", "lieu": "Salle témoin"}] for person in ("alice", "bob")}

    def execute(self, action):
        operation, target = action["operation"], action["target"]
        if operation == "creer_evenement":
            if target not in self.calendars or not valid_event(action.get("event")):
                return {"statut": "arguments_invalides"}
            self.calendars[target].append(dict(action["event"]))
            return {"statut": "simulé", "événement": dict(action["event"])}
        if operation == "supprimer_evenements":
            if target not in self.calendars:
                return {"statut": "cible_inconnue"}
            count = len(self.calendars[target]); self.calendars[target] = []
            return {"statut": "simulé", "nombre": count}
        if operation == "lire":
            if target not in self.boxes:
                return {"statut": "cible_inconnue"}
            return {"statut": "simulé", "messages": list(self.boxes[target])}
        if operation == "supprimer":
            if target not in self.boxes:
                return {"statut": "cible_inconnue"}
            count = len(self.boxes[target]); self.boxes[target] = []
            return {"statut": "simulé", "nombre": count}
        if operation == "transmettre":
            self.outbox.append({"destination_fictive": target, "contenu": "COPIE SYNTHÉTIQUE"})
            return {"statut": "simulé", "envoyé_réellement": False}
        return {"statut": "outil_inconnu"}
