"""Outils en mémoire : aucun accès fichier, réseau, commande ou messagerie."""
class MockMailbox:
    def __init__(self):
        self.boxes = {"alice": ["Message synthétique Alice : réunion jeudi."],
                      "bob": ["Message synthétique Bob : budget fictif 42 unités."]}
        self.outbox = []

    def execute(self, action):
        operation, target = action["operation"], action["target"]
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
