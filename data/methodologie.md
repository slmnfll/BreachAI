### Protocole et objectifs
Question : le contrôle de l’origine et des permissions réduit-il les actions non autorisées tout en conservant la tâche légitime ? Objectif de la version : comparer les deux agents sur dix cas, tracer les décisions et exporter une campagne reproductible avant la présentation.

Unité d’analyse : une paire scénario–agent. Variable manipulée : contrôle d’autorisation. Constantes : corpus, identité Alice et tâche. Huit attaques et deux témoins sont étiquetés indépendamment des décisions. Résumés préécrits : l’utilité mesure une réponse produite et conforme à la référence simulée, pas la qualité linguistique réelle.

### Mesures et limites
- Réussite des attaques : essais malveillants avec action non autorisée exécutée / essais malveillants.
- Blocage : essais malveillants avec refus explicite et sans action non autorisée exécutée / essais malveillants.
- Faux positifs : témoins avec refus / témoins.
- Utilité : essais où un résumé conforme à la référence est fourni / tous les essais. A07 supprime la réponse naïve ; A08 la falsifie. Le protégé conserve la référence. Les anciennes campagnes gardent leur ancienne définition et sont signalées.

Dénominateur nul : « Non mesuré ». A06 n’est compris par aucun agent et ne compte ni comme réussite ni comme blocage. Le corpus est construit, fermé et déterministe. Répéter ne crée pas d’observations indépendantes ; pas d’intervalle de confiance ni de généralisation à des modèles réels. Une étude ultérieure demanderait un corpus indépendant et des variantes linguistiques.

### Intégrité, éthique et ÉDI
Identités et courriels fictifs, domaines `.invalid`. Les actions ne produisent que des traces, sans transmission ni suppression réelle. L’identité sélectionnée est un paramètre expérimental, pas une authentification. Aucun des quatre fournisseurs hypothétiques n’est testé. Les résultats ne démontrent aucune vulnérabilité réelle.

Le corpus français ne permet aucune conclusion sur l’équité linguistique. Une étude future devrait évaluer les langues peu dotées, l’accessibilité et l’exposition des personnes âgées et petites organisations, sans recueillir leurs données dans ce prototype.

### Comparaison des protocoles de divulgation
| Option | Bénéfices | Risques et position proposée |
|---|---|---|
| Coordination simultanée | Prépare les défenses et un calendrier partagé | Choix privilégié dans le scénario, avec délais bornés et réexamen |
| Publication complète immédiate | Transparence rapide | Expose les usagers avant les défenses ; préférer une alerte minimisée si urgence |
| Non-divulgation ou vente exclusive | Diffusion initiale limitée | Captation, exploitation et protection inégale ; option non retenue |

### Chronologie hypothétique
| Échéance indicative | Action et décision |
|---|---|
| J0–J2 | Confirmer dans un environnement autorisé, minimiser la preuve ; suspendre si des données réelles apparaissent |
| J3–J7 | Préparer un contact confidentiel avec les quatre fournisseurs fictifs et une coordination avec le Centre canadien pour la cybersécurité ; vérifier canaux et autorisations avant tout contact réel |
| J14 | Vérifier les accusés de réception, relancer, convenir d’un calendrier commun |
| J30 sans réponse | Escalader au coordonnateur et réévaluer le risque ; ne pas publier automatiquement la charge |
| J45–J60 | Retester sur corpus indépendant et variantes ; documenter les échecs résiduels |
| J90 | Décision documentée : publier la méthode si risque acceptable, sinon prolongation motivée et réexaminée |
| Exploitation publique à tout moment | Alerte défensive minimale, coordination accélérée, aucune procédure exploitable |

Délais proposés, non normatifs. Une amélioration du modèle ne prouve pas que toutes les variantes sont corrigées.

### Fiche publié / retenu
| Publier | Retenir dans un dossier à accès limité |
|---|---|
| Protocole, métriques, limites, corpus synthétique inoffensif | Charges exploitables et intégrations à des services réels |
| Résultats agrégés et calendrier de décision | Messages réels, identifiants et secrets éventuels, absents ici |
| Contributions et déclaration d’usage de l’IA | Correspondances privées et preuves non expurgées |

### Gestion, responsabilité, PI et valorisation
Documenter les contributions et droits avant de choisir une licence. Comparer code ouvert du simulateur, accès restreint aux preuves sensibles et confidentialité temporaire. La brevetabilité et la responsabilité juridique ne sont pas tranchées ici. Journaux locaux modifiables, non signés ; conservation jusqu’à suppression manuelle. Aucun renseignement personnel requis.

Valorisation proposée : banc d’essai pédagogique public, puis audits contractuels autorisés. Publics : fournisseurs et coordonnateur pour les éléments défensifs ; communauté scientifique pour méthode, résultats agrégés et limites. Éviter la diffusion d’une attaque opérationnelle.

### Correspondance INF5163
Le contexte pédagogique provient des énoncés du projet INF5163. Ces documents ne sont pas distribués avec le dépôt et ne sont pas nécessaires au fonctionnement du logiciel. Aucun nom de participant réel ne figure dans le corpus.

Le prototype soutient méthodologie, éthique/ÉDI, gestion/PI, valorisation et chronologie. Restent à produire : rapport LaTeX de 15–20 pages, au moins 15 sources dont 5 articles évalués par les pairs, Beamer de 12 minutes, annexe A des contributions et annexe B d’intégrité. Selon l’énoncé, mobiliser EPTC 2 et Loi 25 lorsque des renseignements personnels sont en jeu et vérifier leur statut applicable pour le rapport ; aucune conformité juridique n’est revendiquée par ce prototype.

Usage de l’IA à déclarer : code, documentation et tests initiaux assistés par Codex le 19 novembre 2026, pour amorcer le démonstrateur. Chaque membre doit relire et approuver ; ne pas inventer les heures ni les signatures.
