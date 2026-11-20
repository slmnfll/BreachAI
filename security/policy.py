"""Décisions sur des actions structurées, jamais sur une identité citée dans un courriel."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Action:
    operation: str
    resource: str
    origin: str

def authorize(action, identity):
    if action.origin != "utilisateur":
        return False, "Instruction issue d’un contenu non fiable : autorité refusée."
    if action.operation != "résumer":
        return False, "Opération absente de la liste des autorisations."
    if action.resource != identity:
        return False, "Ressource appartenant à une autre identité."
    return True, "Résumé autorisé de la boîte synthétique de l’utilisateur."


def authorize_tool(action, identity, task, created=0):
    """Permissions venant de la tâche utilisateur, jamais de la sortie du modèle."""
    if task != "calendar" or action["operation"] != "creer_evenement":
        return False, "Cette opération n’est pas autorisée par la tâche utilisateur."
    if action["target"] != identity:
        return False, "Le calendrier appartient à une autre identité."
    if created >= 1:
        return False, "Un seul événement est autorisé pour cette tâche."
    from security.mock_tools import valid_event
    if not valid_event(action.get("event")):
        return False, "Les champs de l’événement sont invalides."
    return True, "Création unique autorisée dans le calendrier de l’utilisateur."
