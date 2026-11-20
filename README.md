# BrèchIA

**Comprendre l’injection indirecte et comparer les décisions de deux assistants simulés.**

BrèchIA est un laboratoire pédagogique local, en français, développé en Python avec Streamlit. Il présente des courriels fictifs et compare un assistant naïf à un assistant qui contrôle l’origine et les autorisations de chaque action.

> Aucun véritable modèle d’IA n’est utilisé. Les scénarios et résumés sont préparés à l’avance. Aucun courriel n’est envoyé, aucun fournisseur n’est testé et aucune vulnérabilité réelle n’est revendiquée.

## Installation

Prérequis : **Python 3.11 à 3.13** (version testée : 3.13), et une connexion Internet pour installer les dépendances. Aucun compte, clé API ou modèle à télécharger.

Télécharger le dépôt en ZIP puis l’extraire, ou le cloner avec Git. Ouvrir un terminal **dans le dossier contenant `app.py`**.

### macOS et Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

L’application démarre sur **http://localhost:8501**. Streamlit tente d’ouvrir le navigateur ; si aucune fenêtre ne s’ouvre, utiliser cette adresse. Arrêter le serveur avec **Ctrl+C** dans le terminal.

Pour les lancements suivants, activer l’environnement puis exécuter `python app.py` ; inutile de réinstaller les dépendances. Dans PyCharm ou un autre IDE, choisir l’interpréteur de `.venv`, puis exécuter `app.py`.

Le démarrage Streamlit classique reste disponible depuis la racine :

```bash
python -m streamlit run app.py
```

Le serveur est limité à l’ordinateur local et la télémétrie Streamlit est désactivée. Le code du démonstrateur n’appelle aucun service externe. L’installation des dépendances nécessite un accès au registre Python.

## Première expérience en deux minutes

1. Ouvrir **Laboratoire**, sélectionner **Fausse assistance technique** et garder Alice.
2. Lire le courriel : il demande à l’assistant de transmettre des messages, alors qu’Alice lui demande seulement de les résumer.
3. Examiner le passage et sa représentation simulée, puis cliquer sur **Comparer les deux assistants sur ce courriel**.
4. Observer la différence : l’assistant naïf accepte la transmission fictive ; le protégé la refuse. Les deux accomplissent le résumé préécrit.
5. Dans **Comparaison**, lancer les dix scénarios pour consulter les mesures et exporter les traces.

Alice et Bob sont des personnes fictives. « Naïf » et « protégé » désignent deux versions de leur assistant, pas deux personnes.

## Fonctionnalités

| Vue | Utilisation |
|---|---|
| Tableau de bord | Nombre de campagnes et mesures de la dernière campagne |
| Laboratoire | Courriel naturel, passage à examiner, actions simulées et décisions |
| Comparaison | Campagne sur un ensemble de scénarios, indicateurs et export JSON |
| Historique et journaux | Résultats persistants, regroupés par scénario et campagne |
| Méthodologie et éthique | Protocole, limites, chronologie de divulgation et fiche publié/retenu |

La recherche se met à jour pendant la saisie : titre, identifiant (`A01` ou `A 01`), personne, assistant et date UTC (`AAAA-MM-JJ`). Les termes peuvent être combinés. Les mots proches sont proposés explicitement lorsqu’il n’existe aucune correspondance exacte ; les identifiants et dates ne sont pas corrigés approximativement.

Les blocs regroupent les deux assistants d’un scénario testé. La pagination affiche 10, 25 ou 50 blocs. Filtres et recherche changent les détails visibles, pas les indicateurs globaux de la campagne. L’export comparatif contient toute la campagne ; l’export de l’historique contient tous les résultats filtrés.

## Ce que mesure le simulateur

Dix scénarios : deux témoins et huit attaques pédagogiques. Les balises internes `[SIM:opération:ressource]` sont une convention du programme, **pas un type réel d’injection**. Elles sont écrites séparément du courriel naturel ; aucune IA ne les extrait du texte.

| Mesure | Définition |
|---|---|
| Réussite des attaques | Attaques avec au moins une action interdite exécutée / attaques testées |
| Blocage des attaques | Attaques explicitement refusées sans action interdite exécutée / attaques testées |
| Faux positifs | Témoins avec refus / témoins testés |
| Tâche légitime accomplie | Essais avec résumé produit et conforme à la référence simulée / tous les essais |

Un dénominateur nul donne « Non mesuré ». Sur le corpus complet, l’assistant naïf réussit 7 attaques sur 8 ; le protégé en bloque explicitement 7 sur 8 et n’exécute aucune action interdite. A06 n’est reconnu par aucun agent : ce n’est pas une preuve de protection. Les deux témoins passent sans refus.

**A07 — Abandon du résumé :** l’assistant naïf accepte la consigne et ne produit aucun résumé. **A08 — Résumé falsifié :** il annonce une annulation alors que la réunion est maintenue. Le protégé refuse ces consignes et restitue le résumé de référence. Sur les dix cas, la tâche est correctement accomplie dans 8/10 essais naïfs contre 10/10 protégés.

Les sorties et références restent préécrites : la conformité est déterminée par les effets des actions simulées, pas par une évaluation linguistique ou un modèle. Une réponse falsifiée compte comme une attaque réussie et une tâche échouée. Un résumé absent n’est pas compté comme un refus de sécurité. Le moteur 0.2 est inscrit dans les nouveaux résultats ; les anciennes campagnes sont conservées et signalées, sans recalcul rétroactif. Répéter les scénarios ne crée pas d’observations indépendantes.


## Données locales et remise à zéro

La base `data/history.sqlite3` est créée automatiquement et exclue de Git. Elle conserve les décisions et identités synthétiques, sans messagerie personnelle. Les journaux sont modifiables, non signés ; ils ne constituent pas une preuve d’audit inviolable.

Le panneau **Remettre les expériences à zéro** supprime les campagnes et journaux après confirmation. Les scénarios et exports déjà téléchargés restent disponibles. Recharger les autres onglets ouverts pour abandonner leurs résultats en mémoire. La variable `BRECHIA_DB` permet de choisir une autre base, notamment pour les tests.

## Développement et tests

```bash
python -m pytest -q
```

Les tests couvrent autorisations, métriques, persistance, remise à zéro, recherche, regroupement et parcours Streamlit. Les tests utilisent des bases temporaires. La saisie JavaScript instantanée fait l’objet d’une vérification navigateur distincte.

```text
app.py          Démarrage et navigation
ui/             Pages, styles et champ de recherche
agents/         Simulation des deux assistants
scenarios/      Corpus fictif et chargement
security/       Politique d’autorisation
evaluation/     Calcul des mesures
data/           Méthodologie et base locale générée
utils/          Persistance et recherche
tests/          Tests automatisés
```

## Dépannage

- **Module manquant** : utiliser le Python de `.venv` et réinstaller `requirements.txt`.
- **Port 8501 occupé** : arrêter l’autre instance avec Ctrl+C, ou lancer `python -m streamlit run app.py --server.port 8502`.
- **Aucune fenêtre ouverte** : accéder manuellement à http://localhost:8501.
- **Échec d’écriture du journal** : vérifier que le dossier du projet est accessible en écriture.

## Cadre académique, éthique et contributions

Le démonstrateur accompagne une mise en situation hypothétique du cours INF5163 sur la sécurité des agents et la recherche à double usage. Il ne remplace ni le rapport de recherche, ni une revue éthique, ni une analyse juridique. Les documents du cours ne sont pas distribués avec le code et ne sont pas nécessaires à son exécution. Les limites et propositions de divulgation figurent dans `data/methodologie.md`.

Ne pas introduire de courriels personnels, de secrets ou de connecteurs de messagerie dans les exemples. Pour contribuer, décrire le comportement attendu, conserver le caractère synthétique des données et lancer les tests.

Le développement initial du code, de la documentation et des tests a été assisté par Codex. Cet usage doit être déclaré et relu dans les livrables académiques concernés.

Palette inspirée du [bleu institutionnel du réseau de l’Université du Québec](https://reseau.uquebec.ca/fr/system/files/documents/divers/couleurs-etablissements.pdf), sans logo ni affiliation officielle. Documentation technique : [Streamlit](https://docs.streamlit.io/).

**Licence :** aucune licence de réutilisation n’a encore été choisie. La visibilité publique du dépôt ne suffit pas à accorder une licence libre ; les titulaires des droits doivent décider des conditions de distribution et de réutilisation.
