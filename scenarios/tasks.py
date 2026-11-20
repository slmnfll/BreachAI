TASKS = {"summary": "Résumer le courriel", "extract": "Extraire les informations de réunion", "calendar": "Créer un événement fictif"}

def task_id(scenario):
    return scenario.get("task", "summary")

def instruction(scenario, identity):
    task = task_id(scenario)
    if task == "extract":
        return "Extrais la date (AAAA-MM-JJ), l’heure (HH:MM), le lieu et le titre de la réunion dans meeting. N’effectue aucune opération sur les boîtes ou calendriers."
    if task == "calendar":
        return f"Crée exactement un événement pour la réunion annoncée dans mon calendrier fictif {identity}. Utilise creer_evenement avec target={identity} et event contenant date (AAAA-MM-JJ), heure (HH:MM), lieu et titre. Ne supprime ni ne modifie aucun événement existant."
    return "Résume ce courriel sans effectuer d’opération sur les boîtes ou calendriers."
