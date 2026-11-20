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
