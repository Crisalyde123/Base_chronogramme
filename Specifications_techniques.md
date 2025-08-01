# Rapport Technique : Système d'Intégration Automatisée des Chronogrammes de Crise

## 1. Vue d'ensemble de l'architecture cible

Ce système met en place un **pipeline automatisé** pour intégrer des
chronogrammes d'exercices de crise à partir de fichiers Excel
hétérogènes. L'architecture est conçue pour **minimiser les
interventions manuelles** tout en restant flexible et traçable,
conformément aux besoins d'une petite structure sans infrastructure
lourde[\[1\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=humaine%20,sans%20infrastructure%20lourde%20%C3%A0%20maintenir).
Le processus complet s'étend depuis la soumission d'un formulaire par
l'utilisateur jusqu'à la mise à jour de bases de données consolidées.
Voici les composants et étapes clés :

-   **Formulaire de soumission** : Un formulaire utilisateur (ex. un
    formulaire web interne) sert de point d'entrée. L'utilisateur y
    fournit les métadonnées du chronogramme (nom de l'exercice, type
    d'établissement, organisation concernée, date/lieu de l'exercice,
    etc.) ainsi que le fichier Excel du chronogramme. La soumission du
    formulaire déclenche automatiquement l'exécution du pipeline Python
    (via un hook type Power Automate ou autre, évitant tout scheduler
    manuel[\[2\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Il%20faut%20prendre%20en%20compte,log%20pour%20pour%20la%20tra%C3%A7abilit%C3%A9)).

-   **Script principal d'orchestration** : Un script Python principal
    est invoqué à chaque nouvelle soumission. Il orchestre les
    différentes **fonctions de traitement** séquentiellement, en passant
    les informations du formulaire et le fichier Excel aux briques
    logicielles appropriées. Ce script assure la coordination générale
    et la gestion des erreurs éventuelles (écriture de logs, arrêt du
    processus en cas d'exception critique, etc.).

-   **Analyse du fichier Excel et extraction du tableau** : Le pipeline
    identifie dans le classeur Excel la feuille pertinente contenant le
    chronogramme, puis localise le tableau principal à l'intérieur de
    cette feuille. Pour ce faire, il privilégie des **heuristiques
    déterministes** (feuille la plus chargée en données, détection de
    mots-clés comme *« chronogramme »* dans le nom de feuille) afin de
    choisir la bonne
    feuille[\[3\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=simples%20pourraient%20suffire,si%20%20plusieurs%20feuilles%20candidates).
    L'usage d'une IA (LLM tel GPT-4.5) est envisagé seulement en second
    recours si la feuille adéquate reste ambiguë ou introuvable via les
    règles
    simples[\[3\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=simples%20pourraient%20suffire,si%20%20plusieurs%20feuilles%20candidates).
    Une fois la feuille identifiée, le script détecte la zone du tableau
    (ligne d'en-tête et dernières lignes de données) en parcourant les
    cellules non vides. Il isole ainsi uniquement les données du
    chronogramme, excluant les éventuelles notes hors-tableau (en-têtes
    de document, commentaires annexes,
    etc.)[\[4\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=feuille,).

-   **Nettoyage et standardisation des en-têtes** : Les en-têtes de
    colonnes du tableau sont analysés puis convertis vers un **schéma
    standard** commun. Le pipeline applique d'abord un *dictionnaire de
    correspondance* pré-établi pour remplacer les intitulés connus par
    leur équivalent standard (par ex., *« Descriptif »* -\>
    *« Contenu »*)[\[5\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Dans%20%20la%20%20pratique%2C,revanche%2C%20%20si%20%20un).
    Pour tout en-tête inconnu du dictionnaire, une requête à l'**API
    GPT-4.5** est effectuée afin de déterminer le champ standard le plus
    pertinent[\[6\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=dictionnaire,par%20ex)[\[7\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%E2%80%9CDestinataire%E2%80%9D%20%C3%A9galement%29,g%C3%A9rant%20les%20cas%20impr%C3%A9vus%20automatiquement).
    L'IA travaille sur la base d'un contexte contrôlé (liste des
    en-têtes trouvés et liste des champs standards attendus) afin
    d'éviter toute hallucination et de s'en tenir aux champs
    autorisés[\[8\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Il%20faudra%20veiller%20%C3%A0%20bien,parmi%20une%20liste%20donn%C3%A9e).
    Une fois le mapping obtenu (par règles ou par IA), le script
    **renomme automatiquement les colonnes** selon les noms standards et
    **supprime les colonnes non requises** dans le format
    cible[\[9\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Renommage%20%20et%20%20suppression,de%20%20traitement%2C%20%20pour).
    Cette étape normalise la structure du tableau pour la suite du
    traitement.

-   **Extraction et nettoyage des données** : Le contenu du tableau
    chronogramme est extrait (via pandas ou openpyxl) et nettoyé. Le
    pipeline **défusionne les cellules** fusionnées dans la zone de
    données (chaque cellule fusionnée est remplie de la valeur
    appropriée) pour obtenir un tableau rectangulaire
    exploitable[\[10\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%C3%89tape%20d%C3%A9finie%C2%A0%20%3A%20%20D%C3%A9tecter,des%20lignes%20vides%2C%20doublons%2C%20etc).
    Il supprime ensuite les **lignes vides** ou lignes non pertinentes
    (par ex. lignes de titre de section *« Phase »* fusionnées sur toute
    la largeur, doublons d'entêtes,
    etc.)[\[11\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Faisabilit%C3%A9%C2%A0%3A%20La%20d%C3%A9tection%20de%20la,Pandas%20ou%20openpyxl%2C%20on%20peut).
    On obtient ainsi une table brute normalisée : chaque ligne
    représente un *inject* (événement du scénario de crise) avec des
    colonnes standard (horodatage, description de l'inject, émetteur,
    destinataire, catégorie, etc. selon le schéma cible). Le maintien de
    l'ordre chronologique natif des injects est assuré en conservant un
    index de tri (ou en s'abstenant de trier les lignes) afin de ne pas
    mélanger la séquence
    temporelle[\[12\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Point%20d%E2%80%99attention%C2%A0%20%3A%20Il%20faudra,pas%20trier%20automatiquement%20le%20DataFrame).

-   **Uniformisation des valeurs de contenu** : Certaines colonnes
    contiennent des valeurs catégorielles ou des libellés qui varient
    selon les fichiers (par ex. type d'inject, modalités de
    transmission, nom d'entité...). Pour ces colonnes, le pipeline
    réalise une **uniformisation sémantique des valeurs** afin
    d'utiliser des référentiels communs. Il dresse la liste des valeurs
    distinctes présentes dans chaque colonne ciblée, puis pour chaque
    valeur brute, il cherche à la remplacer par une valeur standard :
    d'abord en consultant un **dictionnaire de synonymes** existant
    (associations déjà connues), ensuite -- pour les nouvelles valeurs
    non couvertes -- en sollicitant GPT-4.5 qui jouera le rôle de
    *copilote*
    intelligent[\[13\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Lister%20les%20valeurs%20distinctes%20,les%20cas%20ambigus%20ou%20inconnus).
    Par exemple, si un fichier contient des valeurs *« Mail »*,
    *« Courriel »* et *« Email »* dans une colonne, l'IA pourra suggérer
    de tout mapper vers *« Email »* (valeur standard
    retenue)[\[14\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Analyse%C2%A0%20%3A%20Cette%20%C3%A9tape%20vise,de%20normalisation%20de%20valeurs%20cat%C3%A9gorielles)[\[15\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Utilisation%20d%E2%80%99un%20LLM%C2%A0%20%3A%20,contexte%20%20industriel%2C%20%20des).
    De même, des catégories comme *« Structurant »* vs *« Majeur »*
    seront uniformisées si elles désignent le même niveau
    d'importance[\[14\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Analyse%C2%A0%20%3A%20Cette%20%C3%A9tape%20vise,de%20normalisation%20de%20valeurs%20cat%C3%A9gorielles).
    Toutes les nouvelles correspondances proposées par l'IA sont
    enregistrées pour enrichir le dictionnaire et éviter de futurs
    appels
    redondants[\[16\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20Constituer%20progressivement%20un,pour%20%20chaque%20%20dataset).
    **À chaque remplacement, le système trace l'opération** (voir
    traçabilité ci-dessous), afin qu'un humain puisse contrôler a
    posteriori ces choix sémantiques.

-   **Enrichissement par métadonnées** : En fin de transformation, le
    pipeline ajoute plusieurs **colonnes de contexte** aux données des
    injects. Il s'agit d'informations issues du formulaire ou dérivées,
    qui ne figuraient pas nécessairement dans le tableau initial, par
    exemple : l'**ID du chronogramme** (identifiant unique de l'exercice
    de crise), le **nom de l'établissement** concerné, le **type
    d'établissement** (catégorie de l'organisation), la **source du
    fichier** (nom du fichier Excel d'origine ou un code) et
    éventuellement un **numéro de séquence** pour chaque
    inject[\[17\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%C3%89tape%20d%C3%A9finie%C2%A0%20%3A%20%20Enrichir,client%29%20concern%C3%A9%20par%20l%E2%80%99exercice)[\[18\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=cl%C3%A9%20primaire%20en%20base%29.%20,L%E2%80%99utilisateur).
    Ces champs supplémentaires permettent de garder le lien entre chaque
    événement et son exercice, de filtrer/analyser par organisation ou
    secteur, et d'assurer une traçabilité de la provenance des
    données[\[18\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=cl%C3%A9%20primaire%20en%20base%29.%20,L%E2%80%99utilisateur)[\[19\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Pratiques%20professionnelles%C2%A0%3A%20L%E2%80%99ajout%20de%20m%C3%A9tadonn%C3%A9es,une%20donn%C3%A9e%20de%20r%C3%A9f%C3%A9rence%20au).
    Par exemple, la colonne *Source* contiendra le nom du fichier ou un
    identifiant de l'exercice, et les colonnes *Établissement* et *Type
    Établissement* seront remplies avec les valeurs fournies dans le
    formulaire de soumission (plutôt que d'essayer de les déduire
    automatiquement, opération jugée peu fiable et qu'on
    évite)[\[20\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=contient%20pas%20explicitement%20cette%20info,X%2C%20Type%20d%E2%80%99%C3%A9tablissement%20%3D%20Y).
    De plus, un **identifiant technique** est attribué à chaque inject
    (souvent un simple auto-incrément ou UUID) pour servir de clé
    primaire dans la base de données, combiné à l'ID du chronogramme. En
    effet, l'ID d'inject présent dans le fichier (s'il existe) n'est
    souvent unique qu'au sein d'un même chronogramme, pas globalement --
    c'est pourquoi on le combine avec un identifiant d'exercice pour
    former une clé composite
    unique[\[21\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=La%20colonne%20ID%20n%27est%20pas,Chronogramme%20et%20l%27id%20de%20l%27injecte)[\[22\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Enfin%2C%20la%20num%C3%A9rotation%20s%C3%A9quentielle%20des,combinant%20num%C3%A9ro%20%2B%20source).

-   **Chargement en base de données** : Le pipeline alimente finalement
    deux bases de données SQLite locales (ou deux ensembles de tables
    dans une même base). La première est une base **métier des
    chronogrammes** qui stocke une entrée par exercice de crise (avec
    les métadonnées du formulaire et des indicateurs globaux). La
    seconde est une base des **données d'injects** consolidées,
    contenant toutes les lignes d'injects de tous les exercices, chacune
    liée à son chronogramme. Le script principal insère d'abord les
    informations du formulaire dans la table des chronogrammes (créant
    un nouvel enregistrement exercice), puis insère l'ensemble des
    injects nettoyés dans la table des événements, avec référence à l'ID
    du chronogramme parent. Cette séparation permet de requêter soit au
    niveau *exercice* (par exemple pour la liste de tous les exercices,
    ou leurs caractéristiques), soit au niveau *événement fin* (par
    exemple pour analyser tous les injects filtrés par type ou par date,
    tous exercices confondus). L'utilisation de SQLite garantit une
    solution légère facilement déployable, tout en étant **ouverte à une
    migration vers PostgreSQL** ultérieurement si les données ou
    l'organisation viennent à croître.

-   **Traçabilité et supervision** : Tout au long du processus, une
    attention particulière est portée à la **traçabilité des
    opérations** et à la possibilité d'intervention humaine. Le pipeline
    maintient un **journal de log** détaillé qui enregistre les étapes
    franchies et les décisions automatiques prises, notamment celles
    pilotées par l'IA. Par exemple, il loguera qu'une colonne *X* a été
    renommée en *Y* via le dictionnaire, ou qu'une valeur *V* a été
    classée comme *Catégorie Z* par l'IA, éventuellement avec un score
    de
    confiance[\[23\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Tra%C3%A7abilit%C3%A9%20%20%2F%20%20logging,de%20stocker%20ces%20informations%20dans).
    En parallèle, le système produit un **fichier de contrôle** (par ex.
    un fichier Excel ou CSV de synthèse) listant toutes les
    modifications de mapping effectuées sur les en-têtes et les valeurs.
    Ce fichier de contrôle sert de base à une **supervision humaine
    différée** : un ingénieur peut le consulter après coup pour vérifier
    les correspondances appliquées. Si certaines associations proposées
    par l'IA semblent erronées, il lui suffit de modifier ce fichier de
    contrôle (par exemple choisir une autre valeur standard pour une
    entrée donnée) -- aucune modification manuelle directe dans la base
    n'est nécessaire. Une procédure permet ensuite d'appliquer ces
    corrections : soit en rejouant le pipeline sur les données sources
    avec le dictionnaire mis à jour, soit via un script de mise à jour
    qui lit le fichier de contrôle édité et **répercute les changements
    dans la base** (par exemple, remplacer toutes les occurrences de
    l'ancienne valeur standard par la nouvelle dans les tables, pour
    l'exercice concerné). Ainsi, le système offre un **retour en
    arrière** et une boucle d'amélioration continue : chaque nouveau
    mapping validé enrichit le dictionnaire pour les prochains
    traitements[\[16\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20Constituer%20progressivement%20un,pour%20%20chaque%20%20dataset),
    et les erreurs peuvent être corrigées a posteriori sans casse. Cette
    approche *« automatique avec filet de sécurité humain »* combine
    efficacité et contrôle qualité, ce qui est recommandé pour le data
    cleaning assisté par
    IA[\[24\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Si%20%20une%20%20interface,en%20%20Python%20%20assez)[\[25\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=recommand%C3%A9e%20dans%20les%20t%C3%A2ches%20de,efficacit%C3%A9%20et%20contr%C3%B4le%20qualit%C3%A9).

**Résumé du flux principal** : *Un utilisateur charge un chronogramme
via un formulaire, déclenchant le pipeline Python. Le fichier Excel est
analysé automatiquement : la bonne feuille est identifiée, les données
tabulaires extraites, nettoyées et transformées pour correspondre à un
schéma commun. Les en-têtes et certaines valeurs sont uniformisés à
l'aide d'un dictionnaire évolutif et de l'IA GPT-4.5 en appui. Des
métadonnées contextuelles sont ajoutées puis les données résultantes
sont insérées dans une base de données SQLite normalisée. Tout le
processus est tracé dans des logs et un fichier de contrôle, permettant
à un humain de comprendre et corriger les décisions de l'IA si
nécessaire. L'ensemble est conçu pour fonctionner de manière robuste,
flexible et transparente, sans nécessiter d'infrastructure complexe,
conformément aux bonnes pratiques de l'ingénierie des données augmentée
par
l'IA[\[26\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Les%20%20enjeux%20%20incluent,Garder%20la%20trace%20des)[\[1\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=humaine%20,sans%20infrastructure%20lourde%20%C3%A0%20maintenir).*

## 2. Arborescence du projet et fichiers attendus

Pour assurer une bonne organisation, le projet est structuré en
différents répertoires et fichiers logiques. Ci-dessous,
l'**arborescence cible** du projet est présentée, suivie de la
description du rôle de chaque composant :

    chronogram_pipeline/               ← Répertoire racine du projet
    ├── README.md                     ← Documentation du projet (description générale, instructions d’exécution)
    ├── requirements.txt              ← Liste des dépendances Python (ex: pandas, openpyxl, openai, etc.)
    ├── chronogram_pipeline/config/                       ← Configuration et ressources statiques
    │   ├── mapping_headers.csv       ← Fichier de correspondance des en-têtes (non standard → standard)
    │   ├── mapping_values.csv        ← Fichier de correspondance des valeurs (colonnes concaténées ou séparées, voir description ci-dessous)
    │   └── schema_definition.yaml    ← (Optionnel) Schéma cible et paramètres (liste des champs standards attendus, types, etc.)
    ├── data/                         ← Données sources et intermédiaires
    │   ├── inputs/                   ← Dossier des fichiers Excel en entrée
    │   │   └── <NomExercice>.xlsx    ← Fichiers Excel de chronogramme déposés (nommés par exercice/établissement)
    │   ├── archive/                  ← Archives des sources brutes et outputs intermédiaires
    │   │   ├── raw_excels/           ← Copies des fichiers Excel originaux (pour conservation)
    │   │   └── cleaned_data/         ← (Optionnel) Exports CSV des tables nettoyées, pour audit manuel si besoin
    │   └── control/                  ← Fichiers de contrôle et journaux de modifications
    │       ├── mappings_log.xlsx     ← Journal des mappings appliqués (en-têtes et valeurs uniformisées) pour revue humaine
    │       └── run_<timestamp>.log   ← Logs détaillés de chaque exécution du pipeline (horodatés)
    ├── output/                       ← Données de sortie finales
    │   └── databases/                ← Bases de données SQLite générées
    │       ├── chronogrammes.db      ← Base SQLite pour les exercices de crise (métadonnées des chronogrammes)
    │       └── injects.db            ← Base SQLite pour les injects (données événementielles consolidées)
    └── src/                          ← Code source Python du pipeline
        ├── main.py                   ← Script principal orchestrant le pipeline complet (point d’entrée déclenché par le formulaire)
        ├── form_handler.py           ← Module de gestion de l’entrée du formulaire (parse les données du formulaire, gère l’upload du fichier Excel)
        ├── excel_parser.py           ← Module de lecture du fichier Excel (détection de la feuille, extraction du tableau principal)
        ├── data_cleaner.py           ← Module de nettoyage des données (défusion des cellules, suppression de lignes/colonnes inutiles)
        ├── standardizer.py           ← Module d’uniformisation (standardisation des en-têtes et des valeurs via dictionnaires + IA)
        ├── enricher.py               ← Module d’enrichissement (ajout des métadonnées contextuelles aux données)
        ├── db_utils.py               ← Module utilitaire pour l’interaction avec la base de données (connexion SQLite, insertion des données, migrations éventuelles)
        ├── logger.py                 ← Module de logging configuré (pour centraliser l’écriture des logs structurés)
        └── correction_tool.py        ← (Optionnel) Script de correction manuelle qui lit le fichier de contrôle et applique des changements en base

**Descriptions des principaux fichiers et dossiers** :

-   **README.md** : Document textuel décrivant l'objectif du projet, son
    architecture, et fournissant des instructions pour installer
    l'environnement Python requis, configurer les clés API (pour
    GPT-4.5) et exécuter le pipeline. Il inclut également un guide
    rapide pour interpréter les logs et utiliser le fichier de contrôle
    pour d'éventuelles corrections manuelles. Ce document est crucial
    pour qu'un développeur reprenant le projet puisse comprendre son
    fonctionnement global et le maintenir facilement.

-   **requirements.txt** : Liste des bibliothèques Python nécessaires.
    On y retrouve typiquement `pandas` (pour la manipulation de données
    Excel), `openpyxl` (ou `xlrd`/`xlsxwriter` selon le moteur utilisé
    par pandas pour lire/écrire Excel), `openai` (client API OpenAI pour
    GPT-4.5) et possiblement d'autres utilitaires (par ex.
    `python-dotenv` pour gérer la clé API, etc.). Le projet cherche à
    limiter les dépendances au strict nécessaire pour rester léger.

-   **chronogram_pipeline/config/** : Ce dossier regroupe les fichiers de configuration et
    de référence utilisés par le pipeline :

-   `mapping_headers.csv` est un fichier CSV (éditable sous Excel)
    contenant le dictionnaire de correspondance des en-têtes de colonne.
    Chaque ligne peut comporter deux colonnes : *En-tête original* et
    *En-tête standard*. On y pré-remplit les synonymes connus (par
    exemple *« Descriptif »*, *« Description de l'inject »* →
    *« Contenu »*). Lorsqu'un nouveau nom d'en-tête inconnu est
    rencontré dans un fichier, le pipeline peut l'ajouter dans ce
    fichier avec la proposition de l'IA, pour qu'un humain la valide ou
    corrige. Ce fichier sert donc à la fois de **référentiel de
    mapping** et de **fichier de contrôle** pour les noms de colonnes.

-   `mapping_values.csv` joue un rôle semblable mais pour les valeurs à
    uniformiser dans certaines colonnes. Une implémentation possible est
    d'avoir trois colonnes : *Colonne* (le nom standard de la colonne,
    ex. \"Type d'inject\"), *Valeur brute* (rencontrée dans un Excel,
    ex. \"MAJEUR\"), *Valeur standard* (valeur uniformisée, ex.
    \"Critique\"). On peut filtrer ce CSV par nom de colonne pour
    obtenir le mapping spécifique. Comme pour les en-têtes, toute
    nouvelle valeur inconnue sera ajoutée avec la correspondance
    suggérée par l'IA, en attente de validation éventuelle.

-   `schema_definition.yaml` (optionnel) pourrait définir formellement
    le schéma cible attendu : la liste des champs standards (en-têtes
    attendus), leur type de données, des contraintes, etc. Ce fichier
    sert de source de vérité pour savoir quelles colonnes garder et à
    quel format. Il peut être utilisé par `standardizer.py` pour valider
    les mappings (par ex. vérifier qu'un nom d'en-tête proposé par l'IA
    fait bien partie de la liste des champs autorisés) et par
    `db_utils.py` pour créer les tables SQLite avec les bons types.
    **NB** : Ce fichier n'est pas strictement nécessaire, mais apporte
    de la clarté sur la structure de données cible et facilite
    d'éventuelles migrations (par exemple pour générer les commandes SQL
    de création de tables).

-   **data/inputs/** : Répertoire où sont déposés les fichiers Excel de
    chronogrammes à intégrer. Selon le mode de déploiement, le
    formulaire peut enregistrer le fichier téléversé directement dans ce
    dossier, ou bien le script principal peut y copier le fichier depuis
    un stockage temporaire. Chaque fichier est idéalement nommé de façon
    informative (ex. *Inondations_Paris2023.xlsx* ou
    *Chronogramme_HôpitalX_2024.xlsx*) afin d'aider à la traçabilité. Le
    pipeline traitera chaque fichier individuellement, puis pourra les
    déplacer vers `archive/raw_excels` une fois ingérés.

-   **data/archive/** : Contient des archives des données sources et
    éventuellement des outputs intermédiaires, à des fins de traçabilité
    et de sauvegarde.

-   `raw_excels/` garde une copie horodatée des Excel bruts importés
    (par exemple on pourrait renommer *Chronogramme_HôpitalX_2024.xlsx*
    en *Chronogramme_HôpitalX_2024_INGEST_20250729.xlsx* en y ajoutant
    la date d'ingestion). Conserver ces sources brutes est une bonne
    pratique pour pouvoir y revenir en cas de doute ou pour rejouer un
    traitement si
    nécessaire[\[27\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=,sache%20ce%20qui%20est%20fait).
    L'espace n'étant pas un problème majeur ici, on choisit de garder
    ces fichiers de manière organisée.

-   `cleaned_data/` peut accueillir des exports des données nettoyées et
    standardisées, par exemple au format CSV ou XLSX, avant leur
    insertion en base. Cette étape est optionnelle dans un
    fonctionnement 100% automatisé, mais très utile si l'on décide
    d'introduire une **validation manuelle avant chargement**. On
    pourrait y placer le tableau final des injects pour vérification, ou
    tout autre extrait utile (ex. la liste des nouvelles valeurs
    détectées). Même en l'absence de validation systématique, ces
    fichiers intermédiaires peuvent aider au débogage pendant le
    développement ou servir d'**archive de référence** pour comparer le
    « avant/après » d'un
    traitement[\[28\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Tester%20%20le%20%20pipeline,mieux%20g%C3%A9rer%20les%20cas%20limites).

-   **data/control/** : Ce dossier centralise les **fichiers de contrôle
    et de log destinés à la supervision humaine**.

-   `mappings_log.xlsx` est un fichier Excel (ou CSV) récapitulatif des
    mappings effectués lors des dernières intégrations. Par exemple, il
    pourra contenir deux onglets : **En-têtes** (listant toutes les
    colonnes originales rencontrées, la correspondance standard
    appliquée, et la méthode -- règle manuelle ou IA -- ayant servi) et
    **Valeurs** (listant pour chaque colonne clé toutes les
    substitutions de valeurs faites, avec éventuellement une indication
    si cela provient du dictionnaire existant ou d'une suggestion IA).
    Ce fichier est mis à jour à chaque nouvelle ingestion : si de
    nouveaux mappings sont générés, ils s'y ajoutent. Il sert de
    **journal lisible** pour l'analyste qui voudrait revoir les
    décisions automatiques. En outre, c'est **éditable** : si l'on
    détecte un mapping erroné, on peut ici remplacer la valeur standard
    proposée par la bonne valeur. Un script (`correction_tool.py`) peut
    ensuite relire ce fichier et appliquer en base les modifications
    manuelles (par ex., corriger toutes les entrées déjà enregistrées
    avec l'ancienne valeur). Ce fichier de contrôle représente donc
    l'interface principale de la **supervision a posteriori** du
    pipeline.

-   `run_<timestamp>.log` correspond aux fichiers de log d'exécution du
    pipeline. Chaque exécution produit un fichier log daté (ou alimente
    un seul fichier log cumulatif suivant la configuration du logger).
    On y inscrit des messages techniques et métier à des niveaux
    appropriés (INFO, WARNING, ERROR...). Ces logs détaillent le
    déroulement de l'ingestion : début/fin de chaque étape, nombre
    d'enregistrements traités, identifiant du fichier en cours, mais
    aussi des messages plus spécifiques comme *« 5 valeurs uniformisées
    dans la colonne 'Type d'inject' (3 via dictionnaire, 2 via IA) »*,
    ou *« Nouvelle correspondance ajoutée : 'PC' → 'Poste de
    Commandement' (suggestion IA) »*. Le format est structuré (par ex.
    JSON ou texte avec horodatage) afin de faciliter une analyse
    automatique si besoin, tout en restant lisible par un humain. En
    développement, on pourra logguer très finement (niveau DEBUG) puis
    réduire le verbosité en
    production[\[29\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=du%20Pipeline%20et%20Cartograp,Le).
    Ces journaux assurent la **traçabilité technique** complète du
    pipeline.

-   **output/databases/** : Ce dossier contient les bases de données
    SQLite, qui sont le **produit final** de l'intégration.

-   `chronogrammes.db` est la base (fichier .db SQLite) contenant les
    informations globales sur chaque exercice de crise (un
    enregistrement par chronogramme). Elle regroupe les métadonnées
    renseignées par le formulaire et quelques champs d'accompagnement
    (voir section bases de données). On peut la considérer comme la base
    *« Chronogrammes »* ou *« Exercices »*.

-   `injects.db` est la base contenant toutes les données détaillées des
    injects de tous les exercices. Elle contient potentiellement un
    grand nombre de lignes (chaque inject de chaque fichier importé).
    Chaque ligne y est enrichie des clés permettant de relier à son
    chronogramme parent. On peut la considérer comme la base
    *« Injects »* ou *« Événements »*. **Note** : selon les préférences,
    on pourrait regrouper ces deux bases en une seule base SQLite avec
    deux tables (Chronogrammes et Injects) liées par clé étrangère. Le
    projet est conçu pour supporter facilement cette fusion ou, au
    contraire, une séparation plus poussée (par ex. une base séparée
    pour des référentiels). L'important est de respecter le schéma
    relationnel décrit plus loin, afin de faciliter une migration
    éventuelle vers PostgreSQL.

-   **src/** : Ce répertoire contient **tout le code source Python**
    organisé en modules, chacun correspondant à une brique fonctionnelle
    du pipeline. Cela favorise la clarté et la maintenabilité, en
    évitant un monolithe illisible. Les principaux modules sont :

-   `main.py` : Point d'entrée du pipeline. Ce script est celui qui est
    appelé lors du déclenchement par le formulaire. Il récupère les
    paramètres de la soumission (éventuellement via des arguments CLI,
    des variables d'environnement ou une petite API selon
    l'implémentation), puis appelle successivement les fonctions
    appropriées des autres modules pour traiter le fichier Excel et
    intégrer les données. Il gère aussi la création d'une session de log
    dédiée. En fin d'exécution, il peut envoyer un compte-rendu (par
    exemple imprimer un message de succès, éventuellement notifier
    l'utilisateur via un mécanisme du formulaire).

-   `form_handler.py` : Contient les fonctions liées à la réception et à
    la préparation des données du formulaire. Par exemple, une fonction
    pour enregistrer le fichier Excel uploadé dans `data/inputs/` et une
    fonction pour insérer les métadonnées du formulaire dans la base
    Chronogrammes (via `db_utils`). C'est ici qu'on construit
    l'enregistrement de l'exercice à partir des champs saisis (nom,
    établissement, etc.), qu'on génère si nécessaire un nouvel ID de
    chronogramme, et qu'on le passe à la base de données.

-   `excel_parser.py` : Ce module regroupe les fonctions de **lecture et
    localisation du tableau Excel**. On y trouve la fonction qui charge
    le classeur (via pandas `read_excel` ou openpyxl directement), la
    fonction `detect_main_sheet` pour identifier la feuille pertinente,
    et la fonction `find_data_table` qui localise la plage du tableau
    (détecte la ligne d'en-tête et la dernière ligne de données). Par
    exemple, `find_data_table` peut parcourir la feuille trouvée jusqu'à
    repérer une ligne contenant plusieurs libellés clés correspondant à
    des en-têtes attendus (ID, Date,
    Description...)[\[30\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%20%3A%20Si%20les,Cette%20m%C3%A9thode%2C%20combin%C3%A9e%20%C3%A0),
    la prendre comme début de tableau, puis repérer la première ligne
    vide qui suit pour déterminer la fin du
    tableau[\[11\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Faisabilit%C3%A9%C2%A0%3A%20La%20d%C3%A9tection%20de%20la,Pandas%20ou%20openpyxl%2C%20on%20peut).
    Ce module peut utiliser openpyxl pour lire finement les cellules
    (notamment pour identifier les cellules fusionnées ou la densité de
    contenu par feuille) que pandas ne permet pas d'analyser avant
    lecture. Le résultat principal produit ici est un DataFrame pandas
    des données brutes du chronogramme, incluant la ligne d'en-tête
    détectée.

-   `data_cleaner.py` : Ce module implémente les fonctions de
    **nettoyage des données brutes** une fois le tableau extrait. On y
    trouve par exemple `unmerge_cells` (qui analyse le DataFrame ou la
    feuille openpyxl pour repérer des cellules fusionnées dans la zone
    du tableau et propager les valeurs sur toutes les lignes
    fusionnées), `drop_empty_rows` (qui élimine du DataFrame les lignes
    entièrement vides ou insignifiantes), `drop_empty_cols` (élimine les
    colonnes entièrement vides, s'il y en a). On peut aussi y inclure
    des règles de nettoyage plus spécifiques, comme la suppression de
    lignes « parasites » : par ex. si une ligne ne contient qu'une
    information de regroupement (type *« Phase 1 »* sur toute la ligne),
    on peut décider de l'enlever des données d'injects, ou au contraire
    de la marquer à part. Ces décisions étant métier-dépendantes, la
    fonction pourrait être configurée via `schema_definition.yaml` pour
    savoir quels motifs de lignes ou de colonnes ignorer. Le nettoyage
    garantit en sortie un DataFrame épuré, prêt pour la standardisation.

-   `standardizer.py` : Module clé du pipeline, il contient les
    fonctions d'**uniformisation sémantique** des données. On peut le
    découper en deux sous-parties : standardisation des **colonnes** et
    standardisation des **valeurs**.
    -   Pour les *colonnes* : la fonction principale peut s'appeler
        `standardize_headers(headers: list) -> list`. Elle prend la
        liste des en-têtes extraits du fichier et renvoie la liste
        correspondante des en-têtes standardisés. Elle s'appuie sur le
        fichier `mapping_headers.csv` (chargé en mémoire sous forme de
        dict Python) comme référence. Pour chaque en-tête original, si
        une correspondance existe dans le dict, elle est utilisée.
        Sinon, la fonction fait appel à
        `gpt_suggest_header(original_header: str, schema: list) -> str`
        qui interroge l'API GPT-4.5. Le prompt fourni au LLM lui décrit
        le contexte (par ex. *« Dans un tableau d'exercice de crise,
        "\<Original Header\>" correspond à quel champ standard parmi la
        liste suivante : \[liste champs\]? Réponds uniquement par le nom
        standard. »*). L'IA renvoie un nom (idéalement l'un des champs
        standard attendus). La fonction ajoute alors ce mapping dans le
        dictionnaire en mémoire (et éventuellement dans
        `mapping_headers.csv` sur disque pour
        persistance)[\[5\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Dans%20%20la%20%20pratique%2C,revanche%2C%20%20si%20%20un)[\[7\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%E2%80%9CDestinataire%E2%80%9D%20%C3%A9galement%29,g%C3%A9rant%20les%20cas%20impr%C3%A9vus%20automatiquement).
        Si l'IA renvoie un nom qui n'est pas reconnu dans le schéma, on
        peut soit le rejeter et marquer l'en-tête comme « non mappé »
        (ce qui déclencherait une alerte manuelle), soit décider
        d'étendre le schéma -- mais cela sortirait du cadre automatique.
        Par prudence, toute colonne non mappée explicitement sera
        **ignorée** lors du chargement final et signalée dans le log de
        traitement[\[31\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=d%E2%80%99%C3%AAtre%20s%C3%BBr%20que%20ces%20colonnes,donn%C3%A9e%20rejet%C3%A9e%20au%20cas%20o%C3%B9)[\[32\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20En%20amont%2C%20bien,dictionnaire%20de%20correspondance%2C%20r%C3%A9duisant%20la).
        Une fois que chaque colonne a un nom standard ou est étiquetée
        \"ignorée\", la fonction renvoie la liste normalisée et peut
        écrire dans les logs les changements effectués (ex. *« Colonne
        "Destinataire / cellule" renommée en "Destinataire" (mapping
        existant) » ou* « Colonne "Récepteur" mappée en "Destinataire"
        via
        IA[\[6\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=dictionnaire,par%20ex) »\*).
        Enfin, une fonction
        `apply_header_mapping(df: DataFrame, mapping: dict) -> DataFrame`
        appliquera concrètement le renommage sur le DataFrame (pandas
        permet de renommer facilement via un dict de mapping).
    -   Pour les *valeurs* : des fonctions gèrent l'uniformisation des
        données dans les colonnes ciblées (celles pour lesquelles on a
        identifié un besoin de standardisation sémantique : typiquement
        catégories d'inject, modalités, noms d'entités...). Par exemple,
        `standardize_column_values(df: DataFrame, col: str) -> DataFrame`
        traitera une colonne donnée. Elle extrait les valeurs distinctes
        présentes (`df[col].unique()`), puis pour chacune décide d'une
        valeur standard. Là encore, elle utilise un dictionnaire de
        correspondance propre à la colonne (extrait de
        `mapping_values.csv` pour cette colonne). Pour chaque valeur :
    -   Si la valeur est déjà dans le dict des synonymes, on prend la
        valeur standard correspondante.
    -   Si elle est nouvelle, on utilise une fonction
        `gpt_suggest_value(col_name: str, raw_value: str, allowed_values: list) -> str`.
        Celle-ci interroge GPT-4.5 en lui donnant éventuellement la
        liste des valeurs standards permises pour cette colonne (si
        connue). Exemple de requête : *« Dans la colonne "Modalité de
        transmission", mappe "SMS " vers l'une des modalités standard
        suivantes : \["Email", "Appel Téléphonique",
        "SMS"\] »*[\[15\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Utilisation%20d%E2%80%99un%20LLM%C2%A0%20%3A%20,contexte%20%20industriel%2C%20%20des).
        L'IA répondra par la modalité standard la plus proche (*« SMS »*
        dans l'exemple). Si la liste des valeurs cibles n'est pas
        fournie (parce qu'on ne la connaît pas exhaustivement), on lui
        demandera une suggestion libre cohérente. Le résultat est pris
        comme valeur standard, ajouté au dict de mapping (et au fichier
        CSV de mapping pour
        conservation)[\[13\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Lister%20les%20valeurs%20distinctes%20,les%20cas%20ambigus%20ou%20inconnus)[\[16\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20Constituer%20progressivement%20un,pour%20%20chaque%20%20dataset).
        Là encore, la fonction journalise l'opération (*« 'réseau
        sociaux' uniformisé en 'Réseaux Sociaux' via IA »*) et marque
        éventuellement d'un flag les valeurs proposées par IA pour
        relecture
        humaine[\[33\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Prudence%20et%20validation%C2%A0%20%3A%20,inclure%20l%E2%80%99humain%20dans%20cette%20boucle).
    -   Une fois le mapping déterminé pour toutes les valeurs de la
        colonne, la fonction remplace dans le DataFrame toutes les
        occurrences selon ce mapping (pandas `replace` ou un `map` sur
        la
        série)[\[34\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Ex%C3%A9cution%20%20technique%C2%A0%20%3A%20,de%20ces%20valeurs%20pour%20audit).
    -   Ce processus est répété pour chaque colonne à uniformiser. Il
        peut être encapsulé dans une fonction globale
        `standardize_values(df: DataFrame, columns: list) -> DataFrame`
        qui appellera `standardize_column_values` sur chaque colonne
        d'intérêt en séquence. La liste des colonnes ciblées peut être
        définie dans la configuration (par exemple dans
        `schema_definition.yaml`, on peut taguer les champs qui ont un
        référentiel de valeurs).

-   `enricher.py` : Contient les fonctions d'**ajout de métadonnées** et
    d'enrichissement final. Par exemple,
    `add_context_columns(df: DataFrame, chrono_id: int, form_info: dict) -> DataFrame`
    va ajouter au DataFrame des injects les colonnes supplémentaires
    *Chronogramme_ID*, *Établissement*, *Type_établissement*, etc., en
    remplissant chaque ligne avec les valeurs appropriées issues du
    formulaire ou générées. Cette étape est simple sur le plan technique
    (remplissage de colonnes avec des valeurs scalaires ou une séquence
    auto-incrémentée), mais importante pour la cohérence de l'analyse
    ultérieure[\[18\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=cl%C3%A9%20primaire%20en%20base%29.%20,L%E2%80%99utilisateur).
    On peut aussi ici ajouter un champ *Numéro_inject* s'il n'existait
    pas dans les données sources : par exemple en réinitialisant un
    compteur à 1 pour le premier inject de l'exercice et en
    l'incrémentant pour chaque ligne, afin d'avoir un ordre naturel.
    Cependant, si un ID d'inject existait déjà dans le fichier (beaucoup
    de chronogrammes ont une colonne d'identifiant ou numéro d'inject),
    on peut choisir de la conserver telle quelle pour ne pas perdre
    l'information
    métier[\[35\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=des%20%20injects%20%20%3A,Indispensable%20pour%20tracer%20la).
    Le module se charge également de calculer des indicateurs globaux si
    souhaité, comme le nombre total d'injects -- ce qui peut être utile
    pour mettre à jour la table Chronogrammes (champ *nb_injects*).

-   `db_utils.py` : Ce module fournit des fonctions pour **interagir
    avec la base de données SQLite**. Il comprend typiquement :
    -   `init_databases()` ou `init_tables()` qui crée les tables SQLite
        si elles n'existent pas déjà, en utilisant le schéma prédéfini.
        Cette fonction exécute les commandes SQL `CREATE TABLE`
        appropriées (via la librairie standard `sqlite3`), en tenant
        compte des clés primaires/étrangères, etc.
    -   `insert_chronogram(record: dict) -> int` qui insère un
        enregistrement dans la table Chronogrammes (à partir d'un
        dictionnaire ou objet contenant les champs du formulaire). Elle
        retourne l'ID (auto-généré) du chronogramme inséré, qui servira
        à lier les injects.
    -   `insert_injects(rows: list[dict])` qui insère en base l'ensemble
        des injects d'un chronogramme. Elle peut être optimisée via des
        opérations en masse (ex: utilisation de `executemany` avec des
        paramètres) pour éviter de faire une requête par ligne. Avant
        l'insertion, on s'assure que chaque dict de `rows` contient bien
        tous les champs requis par la table (y compris l'ID du
        chronogramme parent). Cette fonction gère également les
        **contraintes d'intégrité** : par exemple, s'assurer que le
        couple (chronogramme_id, numero_inject) est unique dans la table
        (sinon, on pourrait avoir un conflit si on insère le même
        chronogramme deux fois sans le purger).
    -   D'autres utilitaires potentiels : `fetch_chronogram(id)` ou
        `update_chronogram_stats(id, nb_injects)` pour mettre à jour le
        nombre d'injects après insertion, etc. Également, des fonctions
        pour ouvrir/fermer la connexion SQLite proprement, gérer les
        transactions (commits/rollbacks) en cas d'erreur afin de garder
        la base dans un état cohérent.

-   `logger.py` : Configure le système de **logging** pour le projet. Il
    définit un logger Python avec un format standard (incluant
    timestamp, niveau, fonction source, message). Il peut être paramétré
    pour écrire simultanément sur la console et dans les fichiers log du
    dossier `data/control/`. On y définit éventuellement plusieurs
    *handlers* et *formatters*. L'objectif est d'avoir un logging
    centralisé et facile d'utilisation par les autres modules : au lieu
    d'utiliser `print()`, les fonctions feront des appels du type
    `logger.info("message")` ou `logger.error("message d’erreur")`, ce
    qui assurera la cohérence et la configurabilité de la journalisation
    (ex. basculer en mode debug en changeant un paramètre).

-   `correction_tool.py` : Script optionnel fournissant un moyen de
    **post-traiter les corrections manuelles**. Si on implémente cette
    logique hors du pipeline principal, ce script pourra être exécuté à
    part par un développeur après avoir modifié `mappings_log.xlsx`. Par
    exemple, il va lire le fichier de contrôle, identifier les
    changements (ex: une valeur standard modifiée pour un certain
    original), puis se connecter à la base `injects.db` et exécuter les
    requêtes `UPDATE` nécessaires pour remplacer l'ancienne valeur
    standard par la nouvelle dans la colonne et les enregistrements
    concernés. Il pourra aussi mettre à jour les dictionnaires CSV en
    conséquence. Ce script offre donc un moyen **semi-automatisé** de
    *redo/undo* après coup, sans nécessiter de tout rejouer depuis le
    début, ce qui est précieux si de nombreux chronogrammes ont déjà été
    chargés et qu'on détecte tardivement une incohérence.

L'ensemble de ces fichiers et modules vise à assurer une **séparation
claire des responsabilités**, rendant le code plus lisible et modulaire.
Un développeur Python reprenant le projet pourra facilement localiser
l'endroit où se fait telle opération (ex. standardisation IA dans
`standardizer.py`) et ainsi modifier ou améliorer le comportement sans
effets de bord. De plus, cette arborescence favorise la **traçabilité**
(avec des logs dédiés, des fichiers de mapping bien identifiés) et la
**maintenabilité** (chaque composant étant isolé, les tests unitaires ou
les modifications futures sont simplifiés). Enfin, notons que cette
structure reste compatible avec une évolution du pipeline : par exemple,
si l'on souhaitait introduire un orchestrateur plus tard (Airflow,
Prefect...), on pourrait conserver ces modules et simplement créer des
tâches orchestrées les appelant.

## 3. Bases de données à construire

Le système s'appuie sur des bases de données SQLite pour stocker les
résultats intégrés. L'usage de SQLite permet de déployer la solution
sans effort (fichiers .db locaux) tout en offrant les fonctionnalités
SQL nécessaires. **Deux domaines** de données principaux sont
distingués, correspondant aux deux phases du processus : 1) les
métadonnées des chronogrammes (niveau exercice), 2) les données
détaillées des injects (niveau événement).

On crée donc deux tables principales (éventuellement dans deux fichiers
de base de données distincts pour bien séparer, ou dans un seul fichier
avec deux tables liées). Les schémas sont pensés dès le départ pour
pouvoir être reproduits sous PostgreSQL le moment venu, sans utiliser de
types ou de fonctionnalités propres à SQLite.

### Table « Chronogrammes » (Exercices)

Cette table contient une **ligne par exercice de crise** (chronogramme)
intégré. Elle regroupe les informations générales issues du formulaire
ainsi que quelques champs d'administration. Schéma proposé :

-   **id_chronogramme** -- *TEXT, PRIMARY KEY*. Identifiant unique du
    chronogramme/exercice (ex. `C001`). Sera utilisé
    comme référence étrangère dans la table des injects.
-   **nom_chronogramme** -- *TEXT, NOT NULL*. Nom ou titre de l'exercice
    de crise. Par exemple *« Exercice Inondation Paris 2023 »*.
    Renseigné via le formulaire.
-   **date_exercice** -- *TEXT*, *NULLABLE*. Date (ou période) à
    laquelle l'exercice a eu lieu. Format texte pour simplicité (ex.
    \"2023-11-05\"), mais pourrait être un type date/time si précisé.
-   **lieu_exercice** -- *TEXT*, *NULLABLE*. Lieu géographique de
    l'exercice (ville/région ou établissement particulier).
-   **etablissement_nom** -- *TEXT*, *NULLABLE*. Nom de l'établissement
    ou organisation ayant conduit l'exercice (ex. le client ou
    l'entité).
-   **etablissement_type** -- *TEXT*, *NULLABLE*. Type ou catégorie de
    cet établissement (ex. *« Hôpital »*, *« Collectivité
    territoriale »*, *« Entreprise privée »*, etc.).
-   **submitter** -- *TEXT*, *NULLABLE*. Nom de la personne ayant soumis
    le formulaire (ou ID utilisateur), si on souhaite tracer qui a
    importé le chronogramme.
-   **date_soumission** -- *TEXT*, *NULLABLE*. Timestamp de l'import
    (généré au moment de l'insertion, pour savoir quand le fichier a été
    intégré).
-   **fichier_source** -- *TEXT*, *NULLABLE*. Nom du fichier Excel
    source ou identifiant de stockage, pour référence. On peut stocker
    uniquement le nom de fichier (ex. \"Inondations_Paris_2023.xlsx\")
    ou un chemin complet. Ceci permet de lier chaque enregistrement à
    son fichier d'origine pour audit.
-   **nb_injects** -- *INTEGER*, *NULLABLE*. Nombre d'injects
    (événements) que contient ce chronogramme, c'est-à-dire le nombre de
    lignes insérées dans la table des injects correspondantes. Ce champ
    sera rempli après l'insertion des injects (comptage), ou via un
    `COUNT` en requête si nécessaire. Il offre un aperçu de la
    taille/complexité de l'exercice et peut faciliter des requêtes (ex.
    trouver les exercices avec plus de N événements).

**Contraintes et index** : la clé primaire est `id_chronogramme`. On
peut ajouter une contrainte d'unicité sur `nom_chronogramme` si on sait
que chaque exercice a un nom unique, mais ce n'est pas garanti (deux
exercices différents pourraient avoir un intitulé similaire, surtout
chez des clients différents). Mieux vaut ne pas l'imposer. En revanche,
on peut indexer des champs fréquemment filtrés, par ex. `date_exercice`,
`etablissement_type` pour des analyses futures.

**Remarque** : Il pourrait être judicieux de normaliser les informations
d'établissement dans une table séparée (table **Établissements**) si
l'on prévoit de multiples chronogrammes liés aux mêmes entités. Cela
éviterait les répétitions et faciliterait la mise à jour d'une info
établissement. Une table *Établissements* contiendrait un
`id_etablissement`, le nom et type (et tout autre attribut pertinent
comme secteur, localisation...), et la table Chronogrammes n'aurait que
`etablissement_id` en clé étrangère. Cependant, étant donné la
volumétrie modeste attendue, on a choisi ici de stocker directement
*nom* et *type* pour simplicité. L'extension vers une table normalisée
reste possible sans refonte majeure.

### Table « Injects » (Événements)

Cette table contient **toutes les lignes d'injects** de tous les
chronogrammes intégrés, avec leurs attributs standardisés. Chaque ligne
correspond à un événement simulé dans un exercice. Schéma générique (à
adapter selon les champs observés dans les chronogrammes) :

-   **id_chronogramme** -- *TEXT, PRIMARY KEY*, **NOT NULL**.
    Référence vers l'exercice parent (l'ID dans la table Chronogrammes).
    Assure le lien de chaque inject à son chronogramme. Idéalement, une
    contrainte FOREIGN KEY (bien que SQLite ne les enforce que si
    activées) garantit que l'ID existe dans Chronogrammes. Un index sera
    mis sur ce champ pour accélérer les jointures.
-   **id_inject** -- *TEXT*, *NULLABLE*. Identifiant ou numéro d'inject
    tel que présent dans le fichier source. Beaucoup de chronogrammes
    attribuent un code ou numéro à chaque inject (ex. *« T1.WEEZER.1 »*
    dans un cas, ou simplement *« 1,2,3... »*). S'il existe, on le
    stocke ici à titre informatif. Sinon, on peut utiliser le champ
    comme numéro de séquence généré (1..N par chronogramme). En base, ce
    champ n'est **pas** unique globalement, mais le couple
    (id_chronogramme, id_inject) devrait l'être. On peut donc définir
    une contrainte d'unicité composite sur (id_chronogramme, id_inject)
    pour éviter d'insérer deux fois le même inject d'un exercice.
-   **horodatage** -- *TEXT*, *NULLABLE*. Champ temporel indiquant quand
    l'inject est censé se produire. Selon les fichiers, cela peut être
    un temps relatif (T0, T0+5min...) ou un horaire absolu. On le stocke
    en texte tel quel, ou si un format commun peut être déterminé on
    peut le convertir (par ex. en nombre de minutes écoulées). Ce champ
    permet de reconstituer l'ordre chronologique si nécessaire, en
    complément du numéro.
-   **description** -- *TEXT*, *NULLABLE*. Le contenu de l'inject,
    c'est-à-dire généralement l'information ou l'événement qui est
    injecté lors de l'exercice. Par exemple *« Message : rupture de la
    digue signalée »*. C'est souvent le champ principal.
-   **emetteur** -- *TEXT*, *NULLABLE*. Qui émet l'inject (acteur
    initiateur) -- standardisé. Par exemple *« Préfecture »*,
    *« Direction »*, etc., uniformisés si besoin (ex. *« DGSI »* vs
    *« Direction sécurité »* seraient unifiés).
-   **destinataire** -- *TEXT*, *NULLABLE*. Qui reçoit l'inject ou à qui
    il est destiné. Même traitement de standardisation que l'émetteur si
    des variations existent (ex. différents acronymes pour une même
    entité).
-   **type_inject** -- *TEXT*, *NULLABLE*. Catégorie ou type de
    l'inject. Par exemple *« Majeur »*, *« Structurant »*, *« Mineur »*,
    ou d'autres qualificatifs. C'est typiquement une colonne à
    normaliser via référentiel (on choisit un vocabulaire standard, par
    ex. 3 niveaux de criticité). Les valeurs insérées ici seront donc
    déjà uniformisées (*« Critique », « Important », « Secondaire »,
    etc.* selon le standard retenu).
-   **modalite** -- *TEXT*, *NULLABLE*. Modalité de transmission de
    l'inject, si applicable. Par ex. *« Email »*, *« Téléphone »*,
    *« Radio »*, etc. Également uniformisée (tous les synonymes ramenés
    à une liste définie).
-   **phase_exercice** -- *TEXT*, *NULLABLE*. Phase de l'exercice à
    laquelle appartient l'inject, si les chronogrammes sont structurés
    en phases. Certains chronogrammes mentionnent des phases ou
    séquences. Si c'est pertinent, on la stocke (normalisée
    éventuellement). Sinon ce champ peut être omis.
-   **observations** -- *TEXT*, *NULLABLE*. Tout autre champ libre
    présent dans les fichiers (commentaires, résultats attendus, etc.)
    qu'on souhaiterait conserver pour référence. On peut regrouper
    plusieurs colonnes mineures du fichier source dans ce champ si elles
    ne sont pas normalisées mais qu'on ne veut pas les perdre.
-   **etablissement_nom** -- *TEXT*, *NULLABLE*. (Redondant) Nom de
    l'établissement associé à l'inject. Ce sera dupliqué pour chaque
    ligne de l'exercice. Cette redondance n'est pas optimale en
    normalisation, mais peut faciliter des exports ou analyses directes
    sans jointure. Optionnellement rempli si utile.
-   **etablissement_type** -- *TEXT*, *NULLABLE*. (Redondant) Type de
    l'établissement, même remarque que ci-dessus.

Les champs exacts peuvent varier en fonction des données réellement
présentes dans tous les chronogrammes. L'objectif est d'avoir un schéma
**large mais standard** couvrant tous les attributs pertinents des
injects. Toute colonne non reconnue dans un fichier sera ignorée à
l'intégration (sauf si on décide d'étendre le schéma pour l'inclure).

**Contraintes** : On définit une **clé étrangère** `id_chronogramme` référant
`Chronogrammes(id_chronogramme)` pour garantir l'intégrité référentielle
(SQLite le permet). Une **clé unique composite** est mise sur
(`id_chronogramme`, `id_inject`) afin d'éviter d'insérer deux fois le
même inject du même exercice, et pouvoir repérer d'éventuels doublons.
Cela signifie qu'on ne pourra pas avoir deux lignes avec le même numéro
d'inject dans le même exercice, ce qui est logique.

On peut également indexer certaines colonnes fréquemment filtrées : par
ex. `type_inject`, `modalite`, `emetteur` si l'on prévoit des analyses
par catégorie, ou encore `etablissement_type` si on laisse ce champ dans
la table injects pour filtrer rapidement tous les injects d'un certain
type d'établissement sans devoir joindre.

### Table « Établissements » (Optionnelle)

Si l'on souhaite normaliser davantage, on peut introduire une table pour
les établissements (clients ou entités liées aux exercices). Elle
contiendrait : - **id_etablissement** -- INTEGER PRIMARY KEY - **nom**
-- TEXT, NOT NULL, unique - **type** -- TEXT, NULLABLE - **secteur** --
TEXT, NULLABLE (par ex. Santé, Industrie, Service public, etc.) -
**remarques** -- TEXT, NULLABLE (toute autre info, ou contact, etc.)

La table Chronogrammes aurait alors une colonne `etablissement_id` au
lieu de stocker nom/type directement, ce qui ferait de
`etablissement_id` une FOREIGN KEY vers Établissements. On éviterait
ainsi la duplication du couple (nom, type) dans chaque Chronogramme.
L'ajout de cette table n'est pas obligatoire initialement, surtout si
les exercices sont tous dans des établissements différents (peu de
recouvrement), mais il prépare mieux l'avenir si le volume augmente.

### Autres tables

Outre ces tables principales, on peut prévoir des tables de
**référentiel** pour garder trace des correspondances (mappings)
appliquées, en plus des fichiers de mapping. Par exemple une table
**Correspondance_EnTetes(id, original, standard, source)** et
**Correspondance_Valeurs(id, colonne, original, standard, source)**. Ici
*source* pourrait indiquer si l'origine est "règle" ou "IA" ou "manuel".
Ces tables serviraient d'audit interne en base des décisions de mapping.
Ce n'est pas requis (puisque les CSV/Excel de mapping jouent ce rôle),
mais cela peut faciliter des requêtes SQL pour retrouver toutes les
transformations effectuées. Si on vise la simplicité et éviter la
redondance, on peut ne pas créer ces tables et s'appuyer sur les
fichiers logs et de contrôle pour la traçabilité.

### Considérations de migration PostgreSQL

Le schéma décrit ci-dessus est **compatible PostgreSQL** sans
modification majeure. Les types utilisés (INTEGER, TEXT) ont leur
équivalent direct. Lors de la migration, on pourra renforcer les types
(ex. stocker les dates en type DATE, scinder horodatage en TIME, etc.,
définir des ENUM pour certaines catégories si souhaité). Les clés
primaires et étrangères seront recréées de même. On veillera simplement
à adapter la syntaxe d'auto-incrémentation (`SERIAL` ou
`GENERATED AS IDENTITY` en PostgreSQL au lieu du ROWID SQLite).

Par ailleurs, pour faciliter la migration, on a isolé l'accès base de
données dans `db_utils.py` : ainsi, on pourrait remplacer les appels
SQLite par des appels psycopg2 (ou SQLAlchemy) assez simplement. Il
suffira d'ajouter une couche de configuration (par exemple, un paramètre
dans `schema_definition.yaml` ou une variable d'environnement) pour
choisir le moteur de base de données. Les requêtes SQL utilisées restent
basiques (INSERT, SELECT, UPDATE) et conformes au standard SQL, ce qui
garantit la portabilité.

Enfin, notons que SQLite sert bien nos contraintes actuelles (monoutil,
petite équipe, pas de serveur à maintenir), tout en offrant un chemin de
croissance. En attendant une migration, on peut exploiter ces bases
SQLite pour nos analyses globales, via des requêtes SQL ou en les
connectant à un outil comme DBeaver ou Excel/PowerBI pour exploitation.

## 4. Développement technique détaillé du pipeline (fonction par fonction)

Dans cette section, nous décrivons en détail chaque **brique logicielle
Python** du pipeline, sous la forme de fonctions ou modules, en
précisant leur rôle, leurs entrées/sorties et leur enchaînement.
L'objectif est de fournir une vue quasi-algorithmique du pipeline, sans
plonger dans le code effectif, afin qu'un développeur puisse implémenter
chaque fonction conformément à sa spécification.

**1.** `process_form_submission(form_data)` -- *Rôle :* Point d'entrée
principal du pipeline, orchestrant le traitement d'un nouveau
chronogramme suite à la soumission du formulaire. *Entrée :* un objet ou
dictionnaire `form_data` contenant les champs du formulaire (métadonnées
saisies par l'utilisateur) ainsi que le fichier Excel uploadé (chemin ou
objet fichier). *Sortie :* aucun retour (les effets sont persistés en
base et dans les fichiers), mais génère des logs et éventuellement un
rapport de succès/échec. *Détails :* Cette fonction est appelée
automatiquement par le système de formulaire (par ex. via un script CLI
ou une requête HTTP). Elle va : - Valider les données du formulaire
(présence des champs obligatoires, type du fichier etc.). - Enregistrer
le fichier Excel soumis dans le dossier `data/inputs/` sous un nom
approprié. - Ouvrir une session de logging (création d'un nouveau
fichier log pour cette exécution). - Insérer les métadonnées du
formulaire dans la base Chronogrammes via
`db_utils.insert_chronogram()`, récupérant l'`id_chronogramme`
assigné. - Appeler séquentiellement les fonctions de traitement sur le
fichier Excel : `detect_main_sheet`, `extract_data_table`,
`clean_data_table`, `standardize_headers`, `standardize_values`, etc. en
passant l'ID du chronogramme et en récupérant le DataFrame transformé à
chaque étape. - Appeler `enrich_data` pour ajouter l'ID chronogramme et
autres contextes dans le DataFrame final. - Insérer les données finales
en base via `db_utils.insert_injects()` (en une transaction). - Mettre à
jour éventuellement le record Chronogrammes (champ nb_injects via
`update_chronogram_stats`). - Appeler `archive_file()` pour déplacer le
fichier Excel original en archive (et libérer `data/inputs/`). - Enfin,
clôturer la session de log en notant le statut (succès ou les erreurs
survenues). En cas d'exception non rattrapée en cours de route, cette
fonction doit gérer la restauration (rollback) de la base si nécessaire
et logguer l'échec.

**2.** `detect_main_sheet(workbook)` -- *Rôle :* Identifier la feuille
du classeur Excel qui contient le chronogramme principal. *Entrée :* un
objet classeur (Workbook openpyxl) ou le chemin du fichier Excel (si la
fonction doit l'ouvrir elle-même). *Sortie :* le nom de la feuille
pertinente (chaîne de caractères), ou directement l'objet feuille si on
utilise openpyxl. *Détails :* Cette fonction examine les différentes
feuilles du classeur selon des critères heuristiques. Par exemple, elle
peut calculer pour chaque feuille le nombre de cellules non vides ou la
surface du plus grand bloc de cellules remplies, et sélectionner celle
ayant la plus forte densité de données (car la feuille du chronogramme
est généralement la plus
remplie)[\[3\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=simples%20pourraient%20suffire,si%20%20plusieurs%20feuilles%20candidates).
Elle peut aussi rechercher des mots-clés dans les noms de feuilles (par
ex. *« Chronogramme »*, *« Exercice »*) ou dans le contenu des premières
cellules de chaque feuille pour détecter des indices. Si une feuille se
démarque nettement, on la choisit. En cas de doute entre plusieurs
candidates (par ex. deux feuilles très remplies), on peut solliciter
l'IA : fournir à GPT-4.5 la liste des noms de feuilles et éventuellement
un échantillon de contenu initial, en lui posant la question de laquelle
semble contenir un chronogramme
détaillé[\[36\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Si%20l%E2%80%99on%20souhaite%20n%C3%A9anmoins%20exploiter,sur%20%20le%20%20nom).
L'IA, entraînée sur le contexte du langage, pourrait reconnaître une
structure de tableau d'événements. Toutefois, cette option IA n'est
utilisée qu'en dernier recours, afin de minimiser les appels coûteux et
incertains là où des règles simples
suffisent[\[3\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=simples%20pourraient%20suffire,si%20%20plusieurs%20feuilles%20candidates).
La fonction loggue sa décision (ex : *« Feuille 'Janvier' sélectionnée
(55 lignes de données) »*) et renvoie le nom choisi.

**3.** `find_data_table(sheet)` -- *Rôle :* Localiser précisément la
plage du **tableau** de données dans la feuille identifiée (début et fin
du tableau). *Entrée :* l'objet feuille Excel (openpyxl Worksheet ou
pandas DataFrame de la feuille entière). *Sortie :* Un tuple délimitant
la zone du tableau, par ex.
`(header_row_index, first_data_row_index, last_data_row_index, first_col_index, last_col_index)`,
ou plus simplement un DataFrame pandas extrait qui contient uniquement
le tableau détecté (en incluant la ligne d'en-tête). *Détails :* Cette
fonction parcourt la feuille afin de repérer la ligne d'en-tête du
tableau. Pour cela, on peut rechercher une ligne qui contient plusieurs
libellés connus ou qui a un certain pattern : typiquement, les en-têtes
de colonnes se distinguent par le fait qu'ils sont du texte (pas
numériques), qu'ils n'ont pas trop de cellules vides entre eux, etc. Une
approche robuste est de préparer une liste de *mots-clés* probables pour
les en-têtes (par ex. *« ID »*, *« Date »*, *« Description »*,
*« Durée »*, etc., d'après le schéma standard) et de trouver une ligne
qui contient au moins X de ces
mots-clés[\[30\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%20%3A%20Si%20les,Cette%20m%C3%A9thode%2C%20combin%C3%A9e%20%C3%A0).
Alternativement, si on a lu la feuille entière avec pandas, on peut
parcourir les premières lignes à la recherche de la plus longue séquence
de colonnes non vides. Une fois la ligne d'en-tête repérée,
`find_data_table` détermine la dernière ligne de données : souvent,
c'est la dernière ligne avant une série de lignes complètement vides ou
avant un changement de format. On peut descendre depuis la fin de la
feuille jusqu'à trouver la dernière ligne non
vide[\[11\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Faisabilit%C3%A9%C2%A0%3A%20La%20d%C3%A9tection%20de%20la,Pandas%20ou%20openpyxl%2C%20on%20peut).
Il faut aussi prêter attention aux éventuelles **lignes de synthèse** ou
de **phase** insérées dans le tableau : par ex. une ligne fusionnée sur
toutes les colonnes indiquant \"*Phase 2 : Scénario X*\". Si de telles
lignes existent, la fonction doit décider de les traiter : soit comme
partie du tableau (en les gardant, potentiellement dans une colonne
'Phase'), soit comme des délimitations à exclure. Ce choix peut être
piloté par la config. Dans un premier temps, on peut choisir de les
exclure des données d'injects (elles ne représentent pas un inject
individuel). Donc la *dernière ligne du tableau utile* pourrait être
juste avant une éventuelle ligne de synthèse finale. La fonction
retourne ensuite la portion de la feuille correspondant au tableau ; si
elle utilise pandas, elle renvoie un DataFrame découpé (`df.iloc` sur
les indices trouvés).

**4.** `extract_data(sheet, table_range)` -- *Rôle :* Extraire les
données du tableau sous forme exploitable (DataFrame pandas), en
appliquant la ligne d'en-tête correcte. *Entrée :* l'objet feuille et
éventuellement la plage (indices) du tableau trouvés par
`find_data_table`. *Sortie :* un DataFrame pandas contenant toutes les
lignes de données avec la première ligne en tant qu'en-tête de colonnes.
*Détails :* Si `find_data_table` a déjà renvoyé un DataFrame filtré,
cette fonction peut être triviale. Sinon, elle utilise les indices (par
ex. skiprows jusqu'à header_row-1, use header_row comme header, nrows
jusqu'à last_data_row) pour lire via `pandas.read_excel` la section
voulue[\[37\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=des%20lignes%20vides%2C%20doublons%2C%20etc).
On s'assure ainsi de ne charger que le tableau et pas les cellules hors
tableau. Le DataFrame résultant contient les colonnes telles qu'elles
apparaissent dans l'Excel (non encore normalisées) et les valeurs brutes
(avec potentiellement des NaN là où il y avait des cellules fusionnées,
etc.).

**5.** `unmerge_cells(df)` -- *Rôle :* Corriger dans le DataFrame les
effets de **cellules fusionnées** dans Excel. *Entrée :* DataFrame des
données brutes (avec éventuellement NaN dû aux fusions). *Sortie :*
DataFrame mis à jour, sans « trous » dus aux fusions. *Détails :* Dans
les chronogrammes, il arrive que certaines cellules soient fusionnées
pour des raisons esthétiques ou de présentation (par exemple, un
intitulé d'étape sur plusieurs lignes, ou une colonne étendue sur deux
colonnes adjacentes avec une seule valeur centrée). Lors de
l'extraction, pandas par défaut ne duplique pas la valeur fusionnée sur
les lignes/colonnes cachées, ce qui se manifeste par des NaN. La
fonction `unmerge_cells` va propager les valeurs vers ces NaN.
Typiquement, on parcourt chaque colonne du DataFrame : si une cellule
est NaN et que la précédente ligne a une valeur non NaN dans cette même
colonne, et si l'on suspecte que c'était une fusion (on peut détecter
cela en openpyxl aussi en vérifiant `Worksheet.merged_cells`), alors on
remplace NaN par la valeur du dessus. Cette logique s'applique
prudemment : par exemple, seulement si l'intégralité de la ligne
précédente était identique (critère fort d'une cellule fusionnée
verticalement). Pour les fusions horizontales (rare dans un tableau de
données sauf entête multi-colonnes), openpyxl nous permettrait de savoir
qu'un certain range était fusionné. On peut alors simplement copier la
valeur principale dans toutes les colonnes fusionnées. Cette étape
assure que chaque ligne est autoportante et complète, évitant de perdre
des informations qui auraient été portées par des cellules fusionnées.

**6.** `clean_data(df)` -- *Rôle :* Nettoyer le DataFrame en supprimant
les **lignes indésirables ou vides** et les **colonnes vides/inutiles**.
*Entrée :* DataFrame brut (en-têtes encore originales à ce stade).
*Sortie :* DataFrame nettoyé. *Détails :* Cette fonction va d'abord
éliminer les lignes sans aucune donnée (NaN partout), qui peuvent
apparaître si le tableau était suivi de lignes vides ou contenait des
espaces inutiles. Ensuite, elle traite les lignes non pertinentes : par
ex. les lignes de type \"*Phase X*\" ou \"*Total*\" si le chronogramme
en contenait. On peut détecter ces lignes si un grand nombre de leurs
cellules sont vides sauf une, ou si elles contiennent des mots-clés
comme \"Phase\", \"TOTAL\", etc. Si l'on décide que ces lignes ne
représentent pas un inject, on les retire. (Dans une version avancée, on
pourrait les conserver dans un champ séparé pour info, mais ici on
simplifie en les excluant.) Côté colonnes, `clean_data` peut supprimer
les colonnes entièrement vides (pandas le fait parfois automatiquement)
ou celles jugées inutiles. Cependant, la suppression de colonnes
\"inutiles\" au sens métier doit idéalement se faire après
standardisation des en-têtes, car c'est plus facile de décider sur les
noms standard que sur les noms originaux. Néanmoins, si dès l'état brut
on identifie des colonnes vides ou des colonnes duplicatives (parfois
des Excel contiennent deux fois la même colonne par erreur), on peut les
éliminer. La fonction renvoie un DataFrame épuré, avec toujours les
en-têtes originaux (on attend la standardisation à l'étape suivante). On
loggue le nombre de lignes enlevées pour transparence (ex : *« 2 lignes
de phase supprimées, 1 ligne vide supprimée »*).

**7.** `standardize_headers(headers_list)` -- *Rôle :* Standardiser les
noms de colonnes en utilisant le dictionnaire de correspondance et l'IA
en fallback. *Entrée :* une liste (ou Index pandas) des en-têtes actuels
du DataFrame (tels que lus du fichier). *Sortie :* une nouvelle liste de
noms de colonnes standardisés, de même longueur, correspondant 1-1 aux
entrées. *Détails :* Cette fonction charge le mapping des en-têtes
depuis `mapping_headers.csv` (par ex. sous forme de dict {original -\>
standard}). Pour chaque élément de `headers_list` : - Si le nom est vide
ou null (il arrive qu'Excel ait des colonnes sans en-tête si mal
formaté), on peut l'ignorer ou le marquer \"Inconnu\". - Si le nom
(après éventuel strip des espaces) est présent dans le dictionnaire, on
récupère le nom standard correspondant. - Sinon, on utilise l'IA via
`gpt_suggest_header`. On lui passe la valeur brute de l'en-tête et
possiblement la liste des champs standards connus (depuis
`schema_definition.yaml`) pour qu'il choisisse l'un d'eux. L'IA renvoie
un nom proposé. Si ce nom fait partie des champs attendus, très bien;
sinon, on pourrait décider de l'accepter comme nouveau champ (mais
préférablement non, on veut idéalement cadrer dans le schéma existant).
S'il renvoie quelque chose d'incongru, on peut en dernière instance
nommer la colonne \"Inconnue_X\" et logguer un avertissement. Dans la
plupart des cas, avec un prompt bien conçu, l'IA devrait mapper vers un
champ
existant[\[8\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Il%20faudra%20veiller%20%C3%A0%20bien,parmi%20une%20liste%20donn%C3%A9e). -
Ajouter la correspondance (original -\> standard) trouvée au dict en
mémoire et en sortie. Également, enregistrer dans `mapping_headers.csv`
la nouvelle association (afin d'enrichir le référentiel pour le
futur)[\[5\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Dans%20%20la%20%20pratique%2C,revanche%2C%20%20si%20%20un). -
Noter si la correspondance provient du dictionnaire ou de l'IA, pour
traçabilité. On peut alimenter un log spécifique (ou le fichier de
contrôle) avec une ligne du type : *« En-tête 'Destinataires potentiels'
-\> 'Destinataire' (via IA) »*.

Après traitement de chaque en-tête, on obtient une liste alignée de noms
standard. Avant de l'appliquer, on peut décider de **supprimer certaines
colonnes** : par exemple, si le nom standard obtenu est \"*IGNORE*\" ou
\"*Inconnu*\", cela signale une colonne qu'on ne souhaite pas conserver
(on aura loggué qu'elle est ignorée). Ou bien, on compare chaque nom
standard à la liste des champs cibles du schéma : si un nom standard
n'en fait pas partie, c'est qu'il est superflu -\> on élimine la colonne
correspondante du DataFrame. Il est plus sûr de supprimer après mapping
car ainsi on ne jette pas une colonne qui aurait pu être utile sous un
nom différent. Cette suppression des colonnes non mappées répond aux
bonnes pratiques ETL : ne charger en base que les attributs utiles, mais
**documenter les données rejetées** pour examen
ultérieur[\[38\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=d%E2%80%99%C3%AAtre%20s%C3%BBr%20que%20ces%20colonnes,donn%C3%A9e%20rejet%C3%A9e%20au%20cas%20o%C3%B9).
Ici la documentation se fait via un log ou le fichier de contrôle (liste
des colonnes ignorées).

Enfin, la fonction renvoie la liste des noms standard finaux (pour les
colonnes gardées). Le DataFrame sera ensuite mis à jour avec ces noms
(via pandas `df.columns = new_headers`).

**8.** `apply_header_standardization(df, headers_mapping)` -- *Rôle :*
(Si non combiné avec la précédente) Appliquer le renommage des colonnes
du DataFrame selon le mapping obtenu. *Entrée :* DataFrame brut, et un
dict mapping {ancien_nom: nouveau_nom} pour chaque colonne à renommer.
*Sortie :* DataFrame avec colonnes renommées (et colonnes inutiles
éventuellement supprimées). *Détails :* Cette opération utilise pandas
`df.rename(columns=mapping)` pour renommer, puis peut faire
`df.drop(columns=cols_to_drop)` pour enlever les colonnes dont on a
déterminé qu'elles ne sont pas nécessaires. Très simple
techniquement[\[9\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Renommage%20%20et%20%20suppression,de%20%20traitement%2C%20%20pour).

**9.** `standardize_values(df, mappings_values)` -- *Rôle :* Uniformiser
les valeurs de certaines colonnes du DataFrame en utilisant les
référentiels/dictionnaires + IA. *Entrée :* DataFrame avec en-têtes
standard, et éventuellement une structure de mappings de valeurs (par
exemple un dictionnaire de dictionnaires, par colonne). *Sortie :*
DataFrame où les valeurs cibles sont remplacées par leurs équivalents
standard. *Détails :* Cette fonction va itérer sur chaque colonne du
DataFrame qui nécessite une uniformisation. La liste de ces colonnes
peut être déterminée de plusieurs façons : soit prédéfinie statiquement
(par exemple \[\"emetteur\", \"destinataire\", \"type_inject\",
\"modalite\"\]...), soit dynamiquement en scannant le DataFrame pour
repérer des colonnes nominales où il y a beaucoup de modalités
distinctes (mais mieux vaut se baser sur la connaissance métier). Pour
chaque colonne `col` identifiée : - Charger le dictionnaire existant
pour cette colonne depuis `mapping_values.csv` (toutes les lignes
correspondant à cette colonne). - Extraire
`valeurs_distinctes = df[col].unique()`. - Pour chaque valeur distincte
non nulle/non vide : - Si la valeur est déjà une clé dans le dict de
correspondance, récupérer la valeur standard cible. - Sinon, appeler
`gpt_suggest_value(col, raw_value)` en fournissant le nom de la colonne
pour contexte et possiblement la liste de valeurs standards déjà connues
pour cette colonne (valeurs du dictionnaire ou d'un référentiel). Le
prompt pourrait être : *« Dans la catégorie "Type d'inject", nous avons
la nouvelle valeur "\<raw\>". À quel type standard connu cela
correspond-il ? Options connues : \[X, Y, Z\]. »*. L'IA répond,
idéalement par l'un des types existants ou propose un nouveau type s'il
juge que ça ne rentre dans aucun (dans ce cas, on pourra soit créer un
nouveau type dans le référentiel, soit mapper par analogie). - Récupérer
la proposition de l'IA et l'utiliser comme `valeur_standard`. Ajouter
(raw -\> valeur_standard) dans le dict (en mémoire et l'écrire dans le
CSV de mapping pour conserver la
trace)[\[13\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Lister%20les%20valeurs%20distinctes%20,les%20cas%20ambigus%20ou%20inconnus)[\[16\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20Constituer%20progressivement%20un,pour%20%20chaque%20%20dataset).
Si l'IA avait proposé quelque chose déjà présent différemment formaté
(ex. \"Reseaux Sociaux\" sans accent pour \"Réseaux Sociaux\"), on peut
harmoniser l'orthographe. - Noter la suggestion dans le fichier de
contrôle (par ex. marquer d'un astérisque ou une colonne \"source=IA\"
pour inciter une vérification humaine
ultérieure)[\[33\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Prudence%20et%20validation%C2%A0%20%3A%20,inclure%20l%E2%80%99humain%20dans%20cette%20boucle). -
Une fois obtenu le mapping complet pour la colonne, appliquer
`df[col].replace(mapping_dict)` pour remplacer toutes les valeurs brutes
par les valeurs standard. - Logguer un petit résumé : *« Colonne
Type_inject : 3 valeurs distinctes uniformisées (dont 1 via IA). »*. Si
des valeurs étaient déjà propres (identiques aux standards), elles
restent inchangées.

Cette procédure se répète pour chaque colonne à uniformiser. En fin de
traitement, le DataFrame contient uniquement des valeurs propres et
cohérentes dans ces colonnes
clés[\[14\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Analyse%C2%A0%20%3A%20Cette%20%C3%A9tape%20vise,de%20normalisation%20de%20valeurs%20cat%C3%A9gorielles).
Les colonnes non concernées (par ex. description textuelle libre)
restent telles quelles.

*Exemple concret:* Supposons la colonne *modalite* contient
`{'Mail ', 'Courriel', 'Email'}` comme valeurs distinctes. Dictionnaire
existant: {\"Mail\": \"Email\", \"Courriel\": \"Email\"}. La fonction va
trim \"Mail \" en \"Mail\" (on peut prévoir de strip les valeurs), voir
que \"Mail\" et \"Courriel\" ont des mappings -\> \"Email\". \"Email\"
est déjà standard. Donc toutes ces valeurs seront remplacées par
\"Email\". L'IA n'a même pas été appelée dans ce cas car tout était
couvert ou déjà
standard[\[39\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Par%20exemple%2C%20%20un%20chronogramme,de%20normalisation%20de%20valeurs%20cat%C3%A9gorielles)[\[40\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=on%20peut%20consulter%20un%20r%C3%A9f%C3%A9rentiel,les%20cas%20ambigus%20ou%20inconnus).

**10.** `enrich_data(df, chrono_id, form_data)` -- *Rôle :* Ajouter les
**colonnes de métadonnées** manquantes à chaque ligne d'inject et
préparer les données finales pour insertion. *Entrée :* DataFrame final
des injects standardisés, l'identifiant du chronogramme créé en base, et
éventuellement le dict des infos formulaire déjà utilisées (nom
établissement, type...). *Sortie :* DataFrame prêt à être chargé en base
(schéma final). *Détails :* Cette fonction effectue principalement des
ajouts de colonnes constantes ou dérivées : - Ajouter la colonne
`chronogramme_id` et la remplir avec la valeur `chrono_id` fourni (pour
chaque ligne). - Si pas déjà présent, ajouter `id_inject` (numéro
local) : soit reprendre la colonne d'identifiant du fichier si existait,
soit générer un numéro de ligne (1,2,3...) pour chaque inject dans
l'ordre actuel. Cela peut se faire simplement via `df.reset_index()` si
l'index initial était séquentiel, ou via `range(1, len(df)+1)`. On
obtient ainsi un identifiant lisible par l'utilisateur pour les injects
au sein de l'exercice. Ce numéro, combiné avec l'ID de l'exercice,
formera une clé
unique[\[21\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=La%20colonne%20ID%20n%27est%20pas,Chronogramme%20et%20l%27id%20de%20l%27injecte).
**Note** : Si la colonne ID existait et contenait déjà des identifiants
(par ex. *T1.WEEZER.1*), on peut choisir de les garder dans `id_inject`
tels quels (en format texte), ou de les remplacer par un simple numéro
si on préfère (en conservant l'ancien ID dans un champ observation). -
Ajouter `etablissement_nom` et `etablissement_type` sur chaque ligne, en
les remplissant avec les valeurs provenant de `form_data` (renseignées
par l'utilisateur lors du dépôt). Cela permet de dupliquer ces infos
pour chaque inject, comme évoqué plus haut, afin de faciliter des
analyses directes sur la table des injects (sans jointure
nécessaire)[\[41\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=permettra%20plus%20tard%20de%20filtrer,le%20pipeline%20de%20chargement%20via).
C'est redondant mais justifié dans un contexte de petite échelle pour
avoir des exports "self-contained". - Ajouter `source_file` (ou nom du
fichier) si utile, mais comme on a l'ID chrono qui peut pointer vers la
table Chronogrammes contenant ce champ, ce n'est pas indispensable dans
chaque ligne. On peut néanmoins le faire si on souhaite pouvoir filtrer
ou séparer les données d'origines différentes sans faire la jointure. -
Tout autre enrichissement global peut être fait ici, par ex. ajouter une
colonne *date_import* (même si redondant avec Chronogrammes), ou un flag
de version, etc., selon les besoins de suivi.

Une fois ces ajouts faits, la fonction peut éventuellement réordonner
les colonnes du DataFrame selon l'ordre du schéma final (d'abord les
clés, puis les attributs principaux, etc.), pour correspondre exactement
à la structure de la table de base de données. Elle renvoie ce DataFrame
enrichi et complet.

**11.** `insert_chronogram_to_db(form_data)` -- *Rôle :* Créer un nouvel
enregistrement dans la table Chronogrammes à partir des données du
formulaire. *Entrée :* dict des champs du formulaire (contenant
nom_chronogramme, date, établissement, etc.). *Sortie :* l'identifiant
(id_chronogramme) de l'enregistrement inséré. *Détails :* Implémentée
via `sqlite3`, cette fonction prépare une requête SQL
`INSERT INTO chronogrammes (...) VALUES (...)` avec les champs
disponibles. Elle insère, fait un commit, et récupère l'ID généré (via
`cursor.lastrowid`). Avant insertion, elle peut effectuer de légères
transformations : par ex., formater la date, nettoyer les strings (trim
des espaces), substituer des valeurs par défaut si nécessaire. Elle gère
aussi les erreurs (si la connexion échoue, etc., bien que sur SQLite ce
soit simple). En cas d'erreur à ce stade (ex. base verrouillée), elle
lève une exception que `process_form_submission` capturera pour arrêter
proprement.

**12.** `insert_injects_to_db(df, chrono_id)` -- *Rôle :* Insérer
l'ensemble des injects d'un chronogramme dans la table Injects de la
base de données. *Entrée :* DataFrame final des injects (après
enrichissement), et l'ID du chronogramme parent. *Sortie :* aucune
(soulève exception si problème). *Détails :* Cette fonction itère sur le
DataFrame ou utilise une exécution en lot pour insérer chaque ligne. On
utilise une transaction pour l'ensemble de l'opération afin de garantir
qu'on n'intègre soit *tout* le chronogramme, soit rien (atomicité). Par
pseudo-code : - Convertir le DataFrame en liste de tuples ou dicts
alignés sur les colonnes de la table. - Exécuter un
`INSERT INTO injects (...) VALUES (...)` pour chaque tuple via
`executemany` ou construire un script multi-lignes. On veille à ce que
`id_chronogramme` soit renseigné (via le paramètre fourni). - Gérer les
contraintes d'unicité : idéalement la contrainte (id_chronogramme,
id_inject) unique devrait empêcher d'insérer un doublon. Si on réimporte
involontairement le même chronogramme deux fois, la deuxième insertion
échouera. On peut intercepter cette erreur SQL pour la logguer comme un
doublon et éventuellement ne rien insérer du tout (roll back). -
Committer la transaction une fois toutes les lignes insérées. - En cas
de succès, calculer le nombre de lignes insérées (len du DataFrame) et
le renvoyer ou l'utiliser pour mettre à jour `nb_injects` dans
Chronogrammes (via un
`UPDATE chronogrammes SET nb_injects = ? WHERE id_chronogramme = ?`). -
Journaliser l'opération (ex : *« 45 injects insérés en base pour
l'exercice ID 17 »*).

**13.** `archive_file(file_path, chrono_id)` -- *Rôle :* Archiver le
fichier source après traitement en le déplaçant/renommant. *Entrée :*
chemin du fichier initial et éventuellement l'ID ou nom du chrono pour
renommer. *Sortie :* nouveau chemin en archive. *Détails :* Cette
fonction utilise par exemple `shutil.move` pour déplacer le fichier de
`data/inputs/` vers `data/archive/raw_excels/`. Elle peut renommer le
fichier en ajoutant l'ID ou la date pour éviter les collisions. Par
exemple, *ExerciceX.xlsx* -\> *ExerciceX_id17_20250729.xlsx*. Cela
permet de garder un historique. On loggue que le fichier a été archivé.

**14.** `log_decision(detail)` -- *Rôle :* (Pseudofonction, en réalité
on utilisera directement logger) Écrire une entrée dans le log de
pipeline. *Entrée :* texte ou structure de log. *Sortie :* n/a (effet
d'écriture). *Détails :* On utilise la configuration de `logger.py`. Des
exemples de log importants durant l'exécution : - *INFO:* Démarrage du
traitement pour fichier X, ID chronogramme assigné = Y. - *INFO:*
Feuille \"Chronogramme\" détectée (heuristique densité). - *DEBUG:*
Ligne en-tête détectée = 5, dernière ligne = 52. - *INFO:* En-têtes
standardisés: \[\"ID\", \"Date\", \"Description\", \"Type_inject\",
\...\]. - *WARNING:* Colonne \"Commentaires\" ignorée (non mappée). -
*INFO:* 2 valeurs distinctes à uniformiser dans \"Type_inject\":
{\"Majeur\", \"Structurant\"} -\> toutes deux mappées vers
\"Critique\". - *INFO:* Valeur \"PC\" mappée vers \"Poste de
Commandement\" par IA, à
vérifier.[\[42\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=d%C3%A9cisions%20automatiques,de%20stocker%20ces%20informations%20dans)[\[43\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=en%20%20Destinataire%20%20,de%20stocker%20ces%20informations%20dans) -
*ERROR:* (s'il y a des erreurs, ex. \"Échec d'insertion en base,
duplication détectée, rollback\...\").

Ces logs sont écrits dans le fichier .log et éventuellement affichés sur
la console si configuré. Ils servent de *trace technique et métier* du
déroulement.

**15.** `gpt_suggest_header(header_name, schema_fields)` -- *Rôle :*
Interroger l'API GPT-4.5 pour obtenir un mapping d'en-tête. *Entrée :*
un nom d'en-tête original (string), la liste des champs standard cibles
connus (liste de strings). *Sortie :* un nom de champ standard suggéré
(string). *Détails :* Cette fonction construit un prompt du style :
*« L'en-tête de colonne* `"`*\<header_name\>*`"` *apparaît dans un
tableau de chronogramme de crise. Voici la liste des champs standards
attendus : \<liste\>. Quel champ correspond le mieux ? Réponds
exactement par le nom du champ standard. »*. On appelle l'API OpenAI
(via la librairie `openai` en mode ChatCompletion par ex.) avec ce
prompt et possiblement quelques exemples dans le contexte pour guider.
On fixe un temperature bas (on veut une réponse déterministe) et on
parse la réponse. Idéalement, on pourrait utiliser la fonctionnalité
*function calling* de GPT-4 pour demander un format JSON, ou vérifier
que la réponse est bien l'un des champs
proposés[\[8\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Il%20faudra%20veiller%20%C3%A0%20bien,parmi%20une%20liste%20donn%C3%A9e).
Une fois obtenu, on retourne la suggestion. S'il y a une incertitude ou
une réponse vague, on peut la rejeter et laisser la colonne non mappée.
Dans la pratique, GPT-4.5 est très capable de ce genre de classification
sémantique[\[44\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=donn%C3%A9es%20h%C3%A9t%C3%A9rog%C3%A8nes,%282024%29%20ont%20explor%C3%A9)[\[45\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=afin%20d%E2%80%99%C3%A9viter%20toute%20hallucination,parmi%20une%20liste%20donn%C3%A9e),
donc on s'attend à des correspondances pertinentes. Cette fonction est
appelée à la volée pour chaque en-tête inconnu, et son résultat est
utilisé directement dans `standardize_headers`.

**16.** `gpt_suggest_value(col_name, raw_value, known_values)` --
*Rôle :* Demander à GPT-4.5 de mapper une valeur catégorielle vers un
référentiel standard. *Entrée :* le nom de la colonne (pour contexte,
ex. \"Type d'inject\"), la valeur brute à mapper (string), et la liste
des valeurs standard déjà connues/acceptables pour cette colonne (peut
être vide si inconnu). *Sortie :* la valeur standard suggérée (string).
*Détails :* Le prompt typique pourrait être : *« Dans le champ*
`<col_name>`*, on a la valeur* `<raw_value>`*. Les valeurs standard
attendues pour ce champ sont : \[liste\]. Donne la valeur standard
correspondante (ou la plus proche). »*. Si la liste est vide, on
pourrait demander *« Suggère la catégorie standard de* `<col_name>` *à
laquelle* `<raw_value>` *appartient. »*. GPT-4.5 fera de la
*catégorisation zero-shot*, c'est-à-dire qu'il essaiera de rapprocher la
valeur d'une des cibles
données[\[15\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Utilisation%20d%E2%80%99un%20LLM%C2%A0%20%3A%20,contexte%20%20industriel%2C%20%20des).
Par exemple, *« réseau sociaux »* ou *« RS »* sera rapproché de
*« Réseaux
Sociaux »*[\[15\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Utilisation%20d%E2%80%99un%20LLM%C2%A0%20%3A%20,contexte%20%20industriel%2C%20%20des).
On parse la réponse de l'IA, on la nettoie (capitaux, accents, etc. pour
correspondre exactement à notre référentiel), puis on la retourne. Comme
mentionné, on notera dans le mapping le fait que cette suggestion vient
de l'IA afin de la faire valider par un humain plus
tard[\[33\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Prudence%20et%20validation%C2%A0%20%3A%20,inclure%20l%E2%80%99humain%20dans%20cette%20boucle).
En cas de réponse floue (par ex. l'IA explique au lieu de donner le mot
attendu), on peut reposer la question en insistant sur le format
(éventuellement en une seule phrase). Dans l'idéal, on contraint le
format via le prompt ou l'API. Par exemple, on peut demander la réponse
en JSON du type `{"standard_value": "..."}` et parser. Cela évite des
réponses alambiquées et facilite
l'extraction[\[8\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Il%20faudra%20veiller%20%C3%A0%20bien,parmi%20une%20liste%20donn%C3%A9e).
Cette fonction est appelée potentiellement plusieurs fois par colonne
s'il y a plusieurs nouvelles valeurs. Pour limiter les appels, on
pourrait optimiser en demandant à GPT de mapper une **liste** complète
de valeurs en une seule
fois[\[15\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Utilisation%20d%E2%80%99un%20LLM%C2%A0%20%3A%20,contexte%20%20industriel%2C%20%20des)
(il sait renvoyer un objet JSON avec toutes les correspondances). Cela
serait plus efficace. On pourrait par exemple fournir la liste de toutes
les valeurs distinctes non trouvées pour une colonne en une requête.
Ceci réduit les coûts et assure la cohérence des mappings.
L'implémentation pourra choisir cette voie groupée.

**17.**
`record_mapping_change(mapping_type, original, standard, source)` --
*Rôle :* Enregistrer une nouvelle correspondance dans le fichier de
mapping et éventuellement dans un log dédié. *Entrée :* type de mapping
(\"header\" ou \"value\" avec nom de colonne), la valeur originale, la
valeur standard, la source de la décision (\"dict\" s'il existait déjà,
\"IA\" si proposé par l'IA, ou \"manual\" si ajusté manuellement).
*Sortie :* aucun. *Détails :* Cette fonction écrit une ligne dans le
fichier CSV approprié (`mapping_headers.csv` ou `mapping_values.csv`).
Par exemple, si `mapping_type=="header"`, on ajoute une ligne
`"Destinataires potentiels";"Destinataire"` dans `mapping_headers.csv`
si elle n'y était pas. Si `mapping_type=="value"`, on ajoute
`"Type d'inject";"STRUCTURANT (clé)";"Structurant"`. On peut aussi
ajouter une colonne \"source\" pour indiquer comment cette
correspondance a été déterminée. En parallèle, on peut ajouter une
entrée dans `mappings_log.xlsx` (s'il est distinct) pour un meilleur
suivi. En effet, le fichier CSV sert de base au programme, tandis que le
XLSX de log sert plutôt au suivi humain. Selon notre organisation, on
peut faire en sorte que `mapping_values.csv` ne contienne que les
correspondances validées, alors que `mappings_log.xlsx` liste toutes les
correspondances rencontrées (y compris les nouvelles en attente de
validation). Dans une approche simple, toutefois, on peut décider que le
CSV est l'unique référence et qu'on y inscrit tout (quitte à ce qu'un
humain l'édite après-coup directement). Dans tous les cas, cette
fonction centralise la logique d'écriture afin de ne pas dupliquer du
code d'accès fichier partout dans le pipeline.

**18.** `generate_control_report(changes_list)` -- *Rôle :* Générer ou
mettre à jour le **fichier de contrôle** synthétique après une
exécution. *Entrée :* une liste d'objets ou un ensemble de données
relatant les changements de mapping effectués lors du run (nouvelles
colonnes standardisées, nouvelles valeurs uniformisées, etc.).
*Sortie :* met à jour `mappings_log.xlsx` (pas de retour spécifique).
*Détails :* À la fin de l'exécution (ou pendant), on accumule les
décisions de l'IA et les transformations appliquées. Cette fonction va
soit créer un fichier Excel multi-onglets, soit remplir un template
existant. Par exemple : - Onglet \"En-têtes\" avec colonnes
\[Chronogramme, Colonne Originale, Colonne Standard, Décision\] où
Décision peut être \"Via dictionnaire\", \"Via IA\", \"Ignorée\". -
Onglet \"Valeurs\" avec \[Chronogramme, Colonne, Valeur Originale,
Valeur Standard, Décision\]. L'identifiant ou nom du chronogramme peut
être inclus pour contextualiser (surtout s'il y a plusieurs fichiers
traités avant revue). Dans notre cas, on traite un chronogramme à la
fois, donc ce champ est optionnel. La fonction renseigne ces tableaux :
pour chaque nouvel mapping, on ajoute une ligne. On peut aussi choisir
d'y ajouter *toutes* les valeurs traitées, pas juste les nouvelles, pour
offrir une vision exhaustive du fichier traité. Cependant, cela peut
vite grossir; on peut donc limiter aux nouveautés ou changements. En
plus, un éventuel onglet \"Logs\" pourrait contenir une version lisible
des logs du run (messages clés), mais c'est redondant avec le .log.
Souvent, on fournira plutôt le .log brut pour enquête technique, et le
fichier de contrôle Excel pour un aperçu fonctionnel des mappings. Le
format Excel étant pratique pour un non-développeur, on mise sur lui
pour la relecture et d'éventuelles modifications. Cette fonction utilise
`openpyxl` ou `pandas.to_excel` pour écrire les données. Elle veille à
ne pas écraser les informations précédentes utiles : par exemple, si
`mappings_log.xlsx` cumule l'historique de tous les fichiers, on append
de nouvelles lignes sans supprimer les anciennes (éventuellement, on
peut marquer quelle exécution a introduit la ligne). Si on préfère un
fichier isolé par exécution, on peut inclure le timestamp dans le nom
(mais alors la supervision est morcelée). Il est plus judicieux d'avoir
un fichier unique cumulatif que l'on versionne si besoin.

**19.** `apply_manual_corrections()` -- *Rôle :* Appliquer en base de
données les corrections manuelles effectuées dans le fichier de
contrôle. *Entrée :* Aucun direct (la fonction ira lire le fichier de
contrôle ou les fichiers de mapping mis à jour). *Sortie :* Aucun (mise
à jour de la base effectuée). *Détails :* Cette fonction correspond au
script `correction_tool.py` évoqué. Elle lit par exemple
`mapping_values.csv` qui a pu être modifié manuellement par un humain
pour corriger une correspondance. Ou bien elle lit `mappings_log.xlsx`
pour trouver les entrées marquées comme corrigées (on pourrait imaginer
que l'humain mette en surbrillance ou ajoute un flag \"Corrigé\" sur
certaines lignes). L'implémentation peut varier, mais admettons qu'on
choisisse la simplicité : on demande à l'utilisateur de directement
éditer `mapping_values.csv` et `mapping_headers.csv` pour corriger ce
qui ne convient pas, puis de lancer `apply_manual_corrections`. Celle-ci
va comparer les mappings actuels avec ceux qui ont servi lors de
l'insertion en base (il faut donc garder quelque part une trace de ce
qui a été appliqué -- par exemple, dans `mappings_log.xlsx` on a
l'historique). Si une divergence est trouvée, c'est qu'une valeur
standard a été changée par l'utilisateur. Il faudra alors : - Ouvrir la
base de données (`injects.db`) et exécuter des requêtes UPDATE sur la
table des injects. Par exemple, si initialement on avait mappé \"PC\"
-\> \"Police\" et que l'utilisateur corrige en \"PC\" -\> \"Poste de
Commandement\", on doit faire
`UPDATE injects SET emetteur = 'Poste de Commandement' WHERE emetteur = 'Police' AND id_chronogramme = X`
(peut-être limiter au chronogramme concerné, ou à tous si c'était
global). On peut trouver les enregistrements à changer en se basant sur
la colonne correspondante. - Faire de même pour les en-têtes si jamais
un en-tête standard a été renommé (mais c'est plus rare car normalement
le schéma standard n'est pas modifié a posteriori, sauf ajout d'un
nouveau champ). - Mettre à jour aussi la table Chronogrammes ou
Établissements si, par exemple, on avait mal identifié l'établissement
(ce cas est moins probable, car c'est fourni manuellement). - Une fois
les modifications en base, mettre à jour de façon pérenne les fichiers
de mapping (ils l'ont été par l'user). - Journaliser les changements
appliqués (par ex. dans un log de correction ou réutiliser le log
normal).

Cette fonction garantit ainsi la **cohérence entre le référentiel de
mapping et les données en base**, même après corrections. C'est une
opération ponctuelle (non automatique, déclenchée manuellement quand
nécessaire).

Chacune des fonctions ci-dessus correspond à un **maillon du pipeline**.
Elles s'enchaînent dans l'ordre logique, orchestrées par
`process_form_submission` (ou via plusieurs sous-appels groupés). Ce
découpage fonctionnel apporte clarté et testabilité : on peut tester
indépendamment `standardize_headers` sur des listes d'en-têtes connues,
ou `detect_main_sheet` sur des classeurs types, etc. En production, la
plupart de ces fonctions écrivent dans les logs les informations utiles,
et utilisent des structures de données en mémoire (DataFrame) pour
passer d'une étape à l'autre sans coupler le tout à des fichiers
temporaires (sauf pour le logging/contrôle).

Il est à noter que certaines optimisations ou variantes sont possibles :
par exemple, intégrer la détection de fin de tableau directement dans la
lecture pandas (via `read_excel(..., skipfooter=n)` si on savait n),
mais ici on a préféré une approche explicite et contrôlée. De même, on
aurait pu utiliser un outil externe comme **eparse** pour détecter le
tableau
automatiquement[\[46\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=,en%20base%20de%20donn%C3%A9es)[\[47\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=feuille,des%20%20zones%20%20hors),
ou **OpenRefine** pour la phase de nettoyage
manuel[\[48\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=corrections%2C%20puis%20exporter%20le%20r%C3%A9sultat,%C3%AAtre%20%20r%C3%A9utilis%C3%A9%20%20programmatiquement),
mais cela introduirait des dépendances supplémentaires ou une
intervention non automatisée. Le choix a été de tout réaliser en Python
natif avec pandas et l'API OpenAI, conformément aux contraintes.

## 5. Directives transverses pour le développement

En complément du pipeline technique, voici des **directives globales**
qui doivent guider le développement et l'exploitation de ce projet, afin
d'assurer sa robustesse, sa maintenabilité et son adéquation aux
contraintes énoncées :

-   **Orchestration simple et autonome :** Le pipeline est orchestré par
    un seul script Python (`main.py`) qui enchaîne les étapes du
    traitement. Il n'y a pas d'outil tiers de scheduling ou de gestion
    de workflows (Airflow, Cron, etc.), ce qui évite de complexifier
    l'infrastructure. Le déclenchement se fait **par le formulaire**
    métier lui-même : lorsqu'un utilisateur soumet un nouveau fichier,
    on appelle le script avec les paramètres
    adéquats[\[2\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Il%20faut%20prendre%20en%20compte,log%20pour%20pour%20la%20tra%C3%A7abilit%C3%A9).
    Cela peut être réalisé via un hook HTTP, une fonction Lambda, un
    script shell appelé par l'application de formulaire, etc., selon le
    contexte. L'important est que le système *réagisse à un événement*
    plutôt que de tourner en tâche planifiée vide (on n'a pas de flux
    continu, mais du *triggered batch* ponctuel). Cette approche
    convient bien à une petite organisation et évite de devoir maintenir
    un scheduler dédié. Il faudra documenter le procédé de déclenchement
    (par ex. *« Lors de l'ajout d'un fichier sur SharePoint via le
    formulaire PowerAutomate, un flux exécute la commande*
    `python main.py --file <path> --meta <...>` *sur le serveur »*).

-   **Journalisation et traçabilité :** La mise en place d'un **logging
    détaillé** est impérative. Chaque étape importante doit être logguée
    avec son horodatage et son
    résultat[\[23\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Tra%C3%A7abilit%C3%A9%20%20%2F%20%20logging,de%20stocker%20ces%20informations%20dans).
    On conservera les logs de plusieurs exécutions pour avoir un
    historique (par rotation ou par datage de fichiers). On inclura dans
    les logs des **métriques** utiles : nombre de feuilles analysées,
    ligne d'en-tête trouvée, nombre de colonnes normalisées, temps pris
    par appel IA, nombre de valeurs uniformisées,
    etc.[\[49\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=un%20%20fichier%20%20de,l%E2%80%99inclure%20dans%20un%20rapport%20d%E2%80%99ex%C3%A9cution).
    Cela aide à surveiller le fonctionnement et à détecter les anomalies
    (ex: si subitement un fichier a un nombre de colonnes ignorées
    inhabituel, le log le montrera, incitant à vérifier). On recommande
    d'utiliser le module standard `logging` de Python, éventuellement
    avec un format JSON pour faciliter une éventuelle exploitation
    automatique. Pour le développement, on active un niveau DEBUG
    verbeux, et en production on pourra réduire au niveau INFO/ERROR
    pour ne pas surcharger
    inutilement[\[29\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=du%20Pipeline%20et%20Cartograp,Le).
    Par ailleurs, la traçabilité passe aussi par la **conservation des
    données brutes** : on ne doit pas supprimer ou écraser un fichier
    source avant d'être sûr qu'il est correctement ingéré et validé.
    D'où l'archivage systématique des fichiers originaux dans
    `data/archive/raw_excels` et la possibilité de sauvegarder les
    exports intermédiaires (CSV nettoyés) au moins tant qu'une
    validation humaine finale n'a pas eu
    lieu[\[27\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=,sache%20ce%20qui%20est%20fait).
    Cette sauvegarde permet également la reproductibilité du pipeline :
    on peut rejouer le traitement sur un même fichier brut et obtenir le
    même résultat (sauf évolution du dictionnaire ou de l'IA, mais ça
    fait partie du versioning à tracer).

-   **Gestion des erreurs et robustesse :** Le code doit être défensif.
    Cela signifie gérer les exceptions à chaque étape critique :
    problème d'ouverture de fichier (fichier corrompu ou mauvais
    format), erreur lors de l'appel API (timeouts, rate-limits de l'API
    GPT), échec d'insertion en base, etc. En cas d'erreur récupérable
    (par ex. l'IA ne parvient pas à donner un mapping acceptable), le
    système doit soit avoir une alternative (fallback plus simple, ou
    laisser la valeur telle quelle) soit au minimum logguer clairement
    le problème et continuer les étapes suivantes sans planter. En cas
    d'erreur fatale (ex. base de données verrouillée, fichier
    illisible), il faut que le script principal attrape l'exception, la
    loggue, et termine proprement en indiquant l'échec, sans laisser de
    transactions ouvertes. Idéalement, si une insertion partielle a eu
    lieu avant un échec, il faudrait annuler (rollback) pour ne pas se
    retrouver avec un enregistrement chronogramme sans ses injects par
    exemple. Une solution simple : ne committer l'insertion chronogramme
    et injects qu'en fin de traitement quand tout le DataFrame est prêt,
    ou utiliser une transaction englobante. Le système doit également
    éviter les **effets de bord** persistants en cas d'échec : par ex.,
    ne pas écrire dans le mapping CSV une correspondance IA si
    finalement on a rollbacké l'insertion en base (ça pourrait être
    trompeur). Mieux vaut d'abord finir le traitement en mémoire, et en
    dernière étape écrire en base et fichiers persistants. Ainsi, si une
    étape préliminaire échoue, rien n'a été modifié sur le disque (sauf
    logs). Cela facilite le *re-run* après correction du problème.

-   **Standardisation du code et documentation :** Le développeur devra
    produire un code clair, idiomatique, avec des **commentaires** aux
    endroits complexes (notamment pour expliquer les heuristiques de
    détection, les prompts d'IA, etc.). Chaque fonction aura une
    docstring décrivant son usage, ses paramètres et son output. Un
    effort de documentation est nécessaire dans un contexte où
    l'ingénieur initial quitte le projet après livraison. En plus de la
    documentation inline, un **guide de développement** (par exemple
    sous forme d'un wiki interne ou du README) doit expliquer
    l'architecture d'ensemble, le rôle de chaque module (en reprenant
    l'essentiel de ce rapport), la procédure d'installation (versions de
    Python et librairies utilisées), et comment ajouter de nouveaux
    mappings ou nouveaux champs au schéma. Il faut anticiper que la
    personne qui reprendra le code n'aura possiblement pas tout le
    contexte : la documentation et la lisibilité du code sont donc tout
    aussi importantes que son fonctionnement. Ce rapport en lui-même
    pourra servir de référence, mais il est utile d'avoir un résumé
    condensé dans le README par exemple.

-   **Conformité aux arbitrages techniques initiaux :** Le développement
    suivra scrupuleusement les choix techniques validés lors de la phase
    de conception (résumés dans le document *« squelette projet »*). En
    particulier : utilisation de **pandas** et **openpyxl** pour le
    parsing Excel, sans chercher à intégrer un outil externe de
    détection de tableaux sophistiqué (pour rester maître de la logique
    et parce que les fichiers ne sont pas uniformément
    balisés)[\[50\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Pour%20les%20premi%C3%A8res%20%C3%A9tapes%20on,tableau%20comme%20c%27est%20tr%C3%A8s%20h%C3%A9t%C3%A9rog%C3%A8ne);
    utilisation de l'**API GPT-4.5** d'OpenAI via des appels Python pour
    les tâches d'interprétation sémantique
    (en-têtes/valeurs)[\[51\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Pour%20les%20IA%20on%20utilisera,5);
    stockage des données dans **SQLite** localement, en prévoyant la
    compatibilité PostgreSQL comme
    décrit[\[52\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Pour%20stocker%20les%20bases%20de,enfin%20migrer%20tout%20%C3%A7a%20versPostgreSQL);
    maintien d'une **trace des modifications** faites par l'IA et par
    les règles, avec possibilité de correction humaine via fichier de
    contrôle[\[53\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Et%20de%20plus%20je%20souhaite,fichier%20je%20fais%20le%20journal).
    Ces points ne sont pas des *objectifs flous* mais bien des exigences
    concrètes à implémenter. Tout écart par rapport à ces arbitrages
    (par ex. changer de technologie ou d'approche) devrait être dûment
    justifié et validé, mais a priori il n'y en aura pas car ils ont été
    posés pour de bonnes raisons.

-   **Intégration de l'IA de manière contrôlée :** L'**IA (GPT-4.5)**
    est un atout pour surmonter l'hétérogénéité des fichiers, mais son
    intégration doit rester *contrôlée et transparente*. Concrètement :

-   On limite son usage aux cas *nécessaires* : identification
    d'en-têtes inconnus et uniformisation de valeurs
    inconnues[\[5\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Dans%20%20la%20%20pratique%2C,revanche%2C%20%20si%20%20un)[\[40\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=on%20peut%20consulter%20un%20r%C3%A9f%C3%A9rentiel,les%20cas%20ambigus%20ou%20inconnus).
    On *n'utilise pas l'IA* là où une règle fixe ou un dictionnaire
    suffit (principe de parcimonie pour réduire coût et
    incertitude)[\[5\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Dans%20%20la%20%20pratique%2C,revanche%2C%20%20si%20%20un)[\[13\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Lister%20les%20valeurs%20distinctes%20,les%20cas%20ambigus%20ou%20inconnus).
    Par exemple, pas de GPT pour trouver la feuille du chronogramme tant
    qu'une heuristique simple marche dans \>90% des
    cas[\[3\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=simples%20pourraient%20suffire,si%20%20plusieurs%20feuilles%20candidates),
    pas de GPT pour nettoyer les blancs ou fusion (des opérations
    purement techniques).

-   On surveille ce que l'IA renvoie : les prompts sont conçus pour
    obtenir des réponses courtes et déterministes (idéalement parmi des
    choix
    proposés)[\[8\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Il%20faudra%20veiller%20%C3%A0%20bien,parmi%20une%20liste%20donn%C3%A9e).
    On évite de lui laisser trop de liberté qui pourrait conduire à des
    erreurs d'interprétation. En sortie de chaque appel, on valide : si
    la réponse ne correspond pas à un champ/valeur attendu, on loggue
    une alerte et on pourra nécessiter une validation humaine.

-   On trace chaque appel à l'IA et sa réponse dans le log ou le fichier
    de contrôle. Il doit être possible plus tard de justifier
    *« pourquoi telle valeur a été transformée ainsi »*. La réponse de
    l'IA peut être conservée textuellement dans le log (ou au moins la
    décision).

-   On gère les éventuelles erreurs d'API (timeouts, dépassement de
    quota) en prévoyant une nouvelle tentative ou en sautant l'étape
    avec un log d'avertissement. Le pipeline ne doit pas planter
    entièrement à cause d'une indisponibilité ponctuelle de l'IA : on
    peut retenter après quelques secondes en cas de timeout, et si
    vraiment l'IA ne répond pas, traiter les colonnes concernées plus
    tard (par ex. marquer les valeurs à uniformiser dans le fichier de
    contrôle pour traitement manuel).

-   Niveau coûts, on peut regrouper les requêtes comme mentionné pour
    minimiser le nombre d'appels. Aussi, si GPT-4.5 est onéreux, on
    pourrait configurer un modèle alternatif (GPT-3.5-turbo) pour
    certaines tâches moins complexes, bien que la précision pourrait en
    souffrir. C'est un paramètre ajustable.

-   Surtout, l'IA n'est jamais utilisée pour prendre une décision finale
    non vérifiable. Toute suggestion de GPT est soit appliquée sur des
    éléments non critiques, soit sujette à validation humaine (directe
    ou a posteriori). On suit donc le principe *Human in the loop* sur
    les aspects sémantiques
    sensibles[\[33\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Prudence%20et%20validation%C2%A0%20%3A%20,inclure%20l%E2%80%99humain%20dans%20cette%20boucle).
    Par exemple, si l'IA interprète mal un acronyme (*« PC »* →
    *« Police »* au lieu de *« Poste de
    Commandement »*)[\[33\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Prudence%20et%20validation%C2%A0%20%3A%20,inclure%20l%E2%80%99humain%20dans%20cette%20boucle),
    le système de supervision doit permettre de corriger cela avant que
    ça n'induise quelqu'un en erreur. En pratique, cela veut dire que
    les utilisateurs finaux des données doivent être informés que
    certaines classifications sont automatiques et potentiellement
    imparfaites, d'où l'importance du fichier de contrôle et des
    éventuelles revues.

-   **Supervision humaine et amélioration continue :** Même si le
    pipeline est conçu pour fonctionner de façon automatique sans
    intervention constante, il s'inscrit dans une démarche
    d'**amélioration continue avec feedback humain**. En plus des
    fichiers de contrôle qui permettent les corrections, il est
    conseillé de mettre en place un processus léger de revue des
    importations. Par exemple, un membre de l'équipe peut vérifier le
    fichier `mappings_log.xlsx` après chaque nouvel exercice intégré (ou
    une fois par semaine s'il y en a beaucoup) pour valider que les
    nouveaux mappings ajoutés sont corrects. S'il y a un doute, on
    ajuste dans le fichier et on relance le script de correction ou on
    note de corriger dans la base via une requête. Cette boucle de
    feedback permettra d'enrichir rapidement les dictionnaires internes,
    de sorte qu'au fil du temps l'IA sera de moins en moins sollicitée
    (seulement pour de vraies
    nouveautés)[\[16\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20Constituer%20progressivement%20un,pour%20%20chaque%20%20dataset).

-   Par ailleurs, on pourrait envisager à terme d'avoir un petit outil
    d'interface (par ex. un dashboard Streamlit) pour visualiser les
    données importées et les valider avant confirmation
    définitive[\[24\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Si%20%20une%20%20interface,en%20%20Python%20%20assez),
    mais cela ajouterait de la complexité et n'est pas requis dès le
    départ. La solution actuelle, basée sur des fichiers de log et de
    mapping, vise la **simplicité et l'auto-contenu** (tout se fait avec
    des fichiers locaux et scripts Python, ce que le prochain
    développeur pourra comprendre sans avoir à maîtriser un framework
    web).

-   L'équipe doit également définir comment réagir en cas de découverte
    d'une erreur tardive (ex: un mapping appliqué depuis longtemps se
    révèle faux). Grâce à la traçabilité en base (chaque inject garde
    l'indication de sa source et on a tous les logs), on pourra soit
    recourir au *reprocessing* (supprimer les données erronées et
    réimporter avec la nouvelle règle) soit au *bulk update* via une
    requête SQL. Notre pipeline favorise le reprocessing reproductible :
    puisque les fichiers sources sont archivés et que les
    transformations sont déterministes (dictionnaires + IA guidée), on
    peut rejouer facilement un traitement complet sur un fichier après
    correction du mapping, assurant que la base reflète la correction
    partout. Cette approche est plus sûre que d'écrire directement dans
    la base, mais pour des modifications mineures globales, le script de
    correction convient.

-   **Autonomie du système et exploitation future :** Le système est
    conçu pour être **autoportant**. Cela signifie qu'une fois déployé
    sur la machine prévue (par exemple le serveur interne ou le PC de
    l'ingénieur data), il peut fonctionner sans surveillance constante.
    Le fait de tout consigner dans des logs, de gérer les erreurs et de
    ne dépendre que d'outils locaux garantit que les importations
    pourront s'enchaîner même en l'absence du développeur. Néanmoins, il
    est prudent de mettre en place quelques garde-fous opérationnels :

-   Surveiller l'espace disque (les fichiers Excel archivés et les bases
    vont grossir avec le temps, mais faiblement étant donné la taille
    modeste de chaque chronogramme).

-   Prévoir une procédure de sauvegarde des bases SQLite régulière (par
    exemple, une copie hebdomadaire du dossier `output/databases`),
    surtout avant une migration éventuelle vers PostgreSQL.

-   Mettre en place une notification en cas d'erreur critique. Par
    exemple, si `process_form_submission` se termine avec une exception,
    on pourrait envoyer un email automatique ou générer une alerte pour
    que quelqu'un intervienne. Sans aller jusqu'à coder un système
    d'alerte complet, cela peut être réalisé via le système de
    formulaire ou un simple script d'analyse des logs (ex. si un log
    ERROR est apparu, notifier).

-   Maintenir les fichiers de configuration à jour : par exemple, si
    l'API OpenAI change de version ou si on souhaite ajuster les
    paramètres des prompts, il faut que le responsable futur sache
    comment faire (d'où l'intérêt de config.yaml pour centraliser de
    tels paramètres).

-   Garder l'évolutivité en tête : si demain on veut intégrer ce
    pipeline dans un environnement cloud ou plus grand, le code
    modulaire facilite la substitution de composants (ex: remplacer
    SQLite par PostgreSQL, pandas par PySpark DataFrame si le volume
    explosait -- même si improbable, on a isolé suffisamment la logique
    pour pouvoir la réécrire avec d'autres outils en s'inspirant des
    mêmes étapes).

-   **Tests et validation initiale :** Avant de passer en production
    (c'est-à-dire d'intégrer de vrais fichiers de façon automatique), il
    est impératif de **tester** le pipeline sur plusieurs exemples de
    chronogrammes représentatifs. On choisira des fichiers variés (ex:
    un chronogramme par type d'exercice ou par client, s'ils diffèrent
    de structure) et on les traitera avec le pipeline. On comparera le
    résultat en base avec les attentes : les champs sont-ils
    correctement peuplés ? Y a-t-il des données perdues ou mal mappées ?
    On ajustera le dictionnaire initial en conséquence, et peut-être les
    règles (par ex. ajouter un mot-clé pour détecter la feuille, affiner
    le prompt de l'IA si on voit une confusion, etc.). Ces tests doivent
    être documentés (par ex. dans un cahier de tests interne).
    L'ingénieur data partant pourra ainsi fournir à son successeur une
    base de quelques fichiers d'exemple et les résultats attendus, pour
    référence. Cela fait partie des bonnes pratiques
    recommandées[\[28\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Tester%20%20le%20%20pipeline,mieux%20g%C3%A9rer%20les%20cas%20limites).

En suivant ces directives, on s'assure que le développement du pipeline
n'est pas seulement un codage rapide pour une démonstration, mais la
construction d'un **système pérenne, robuste et compréhensible**.
L'accent est mis sur la **simplicité pragmatique** (pas de
micro-services ou d'orchestrateurs externes complexes dans un contexte
où ce serait surdimensionné), l'**ouverture** (on utilise des formats
simples comme CSV, SQLite, facilement interrogeables, et on peut évoluer
vers plus grand si besoin), et la **transparence** (chaque
transformation est tracée et explicable). En somme, ce pipeline
s'inspire des pratiques professionnelles en data engineering adaptées à
une petite
échelle[\[26\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Les%20%20enjeux%20%20incluent,Garder%20la%20trace%20des),
tout en tirant parti de l'IA de manière ciblée pour gagner en
flexibilité[\[54\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=s%E2%80%99inspirant%20des%20pratiques%20professionnelles%20en,Ad%C3%A9quation%20%20%C3%A0).
Ce sera un outil autonome qui, une fois paramétré, pourra intégrer de
nouveaux fichiers de chronogrammes d'un simple clic sur un formulaire,
fournissant en sortie des données uniformisées prêtes pour l'analyse
globale, et ce *même en l'absence de l'ingénieur initial*.

[\[1\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=humaine%20,sans%20infrastructure%20lourde%20%C3%A0%20maintenir)
[\[3\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=simples%20pourraient%20suffire,si%20%20plusieurs%20feuilles%20candidates)
[\[4\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=feuille,)
[\[5\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Dans%20%20la%20%20pratique%2C,revanche%2C%20%20si%20%20un)
[\[6\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=dictionnaire,par%20ex)
[\[7\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%E2%80%9CDestinataire%E2%80%9D%20%C3%A9galement%29,g%C3%A9rant%20les%20cas%20impr%C3%A9vus%20automatiquement)
[\[8\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Il%20faudra%20veiller%20%C3%A0%20bien,parmi%20une%20liste%20donn%C3%A9e)
[\[9\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Renommage%20%20et%20%20suppression,de%20%20traitement%2C%20%20pour)
[\[10\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%C3%89tape%20d%C3%A9finie%C2%A0%20%3A%20%20D%C3%A9tecter,des%20lignes%20vides%2C%20doublons%2C%20etc)
[\[11\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Faisabilit%C3%A9%C2%A0%3A%20La%20d%C3%A9tection%20de%20la,Pandas%20ou%20openpyxl%2C%20on%20peut)
[\[12\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Point%20d%E2%80%99attention%C2%A0%20%3A%20Il%20faudra,pas%20trier%20automatiquement%20le%20DataFrame)
[\[13\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Lister%20les%20valeurs%20distinctes%20,les%20cas%20ambigus%20ou%20inconnus)
[\[14\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Analyse%C2%A0%20%3A%20Cette%20%C3%A9tape%20vise,de%20normalisation%20de%20valeurs%20cat%C3%A9gorielles)
[\[15\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Utilisation%20d%E2%80%99un%20LLM%C2%A0%20%3A%20,contexte%20%20industriel%2C%20%20des)
[\[16\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20Constituer%20progressivement%20un,pour%20%20chaque%20%20dataset)
[\[17\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=%C3%89tape%20d%C3%A9finie%C2%A0%20%3A%20%20Enrichir,client%29%20concern%C3%A9%20par%20l%E2%80%99exercice)
[\[18\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=cl%C3%A9%20primaire%20en%20base%29.%20,L%E2%80%99utilisateur)
[\[19\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Pratiques%20professionnelles%C2%A0%3A%20L%E2%80%99ajout%20de%20m%C3%A9tadonn%C3%A9es,une%20donn%C3%A9e%20de%20r%C3%A9f%C3%A9rence%20au)
[\[20\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=contient%20pas%20explicitement%20cette%20info,X%2C%20Type%20d%E2%80%99%C3%A9tablissement%20%3D%20Y)
[\[22\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Enfin%2C%20la%20num%C3%A9rotation%20s%C3%A9quentielle%20des,combinant%20num%C3%A9ro%20%2B%20source)
[\[23\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Tra%C3%A7abilit%C3%A9%20%20%2F%20%20logging,de%20stocker%20ces%20informations%20dans)
[\[24\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Si%20%20une%20%20interface,en%20%20Python%20%20assez)
[\[25\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=recommand%C3%A9e%20dans%20les%20t%C3%A2ches%20de,efficacit%C3%A9%20et%20contr%C3%B4le%20qualit%C3%A9)
[\[26\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Les%20%20enjeux%20%20incluent,Garder%20la%20trace%20des)
[\[27\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=,sache%20ce%20qui%20est%20fait)
[\[28\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Tester%20%20le%20%20pipeline,mieux%20g%C3%A9rer%20les%20cas%20limites)
[\[29\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=du%20Pipeline%20et%20Cartograp,Le)
[\[30\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%20%3A%20Si%20les,Cette%20m%C3%A9thode%2C%20combin%C3%A9e%20%C3%A0)
[\[31\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=d%E2%80%99%C3%AAtre%20s%C3%BBr%20que%20ces%20colonnes,donn%C3%A9e%20rejet%C3%A9e%20au%20cas%20o%C3%B9)
[\[32\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Optimisation%20propos%C3%A9e%C2%A0%3A%20En%20amont%2C%20bien,dictionnaire%20de%20correspondance%2C%20r%C3%A9duisant%20la)
[\[33\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Prudence%20et%20validation%C2%A0%20%3A%20,inclure%20l%E2%80%99humain%20dans%20cette%20boucle)
[\[34\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Ex%C3%A9cution%20%20technique%C2%A0%20%3A%20,de%20ces%20valeurs%20pour%20audit)
[\[35\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=des%20%20injects%20%20%3A,Indispensable%20pour%20tracer%20la)
[\[36\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Si%20l%E2%80%99on%20souhaite%20n%C3%A9anmoins%20exploiter,sur%20%20le%20%20nom)
[\[37\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=des%20lignes%20vides%2C%20doublons%2C%20etc)
[\[38\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=d%E2%80%99%C3%AAtre%20s%C3%BBr%20que%20ces%20colonnes,donn%C3%A9e%20rejet%C3%A9e%20au%20cas%20o%C3%B9)
[\[39\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=Par%20exemple%2C%20%20un%20chronogramme,de%20normalisation%20de%20valeurs%20cat%C3%A9gorielles)
[\[40\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=on%20peut%20consulter%20un%20r%C3%A9f%C3%A9rentiel,les%20cas%20ambigus%20ou%20inconnus)
[\[41\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=permettra%20plus%20tard%20de%20filtrer,le%20pipeline%20de%20chargement%20via)
[\[42\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=d%C3%A9cisions%20automatiques,de%20stocker%20ces%20informations%20dans)
[\[43\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=en%20%20Destinataire%20%20,de%20stocker%20ces%20informations%20dans)
[\[44\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=donn%C3%A9es%20h%C3%A9t%C3%A9rog%C3%A8nes,%282024%29%20ont%20explor%C3%A9)
[\[45\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=afin%20d%E2%80%99%C3%A9viter%20toute%20hallucination,parmi%20une%20liste%20donn%C3%A9e)
[\[46\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=,en%20base%20de%20donn%C3%A9es)
[\[47\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=feuille,des%20%20zones%20%20hors)
[\[48\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=corrections%2C%20puis%20exporter%20le%20r%C3%A9sultat,%C3%AAtre%20%20r%C3%A9utilis%C3%A9%20%20programmatiquement)
[\[49\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=un%20%20fichier%20%20de,l%E2%80%99inclure%20dans%20un%20rapport%20d%E2%80%99ex%C3%A9cution)
[\[54\]](file://file-Wq7nEwUX7m8MFTB1pnCVXa#:~:text=s%E2%80%99inspirant%20des%20pratiques%20professionnelles%20en,Ad%C3%A9quation%20%20%C3%A0)
Intégration Automatisée des Chronogrammes d'Exercices de Crise --
Évaluation du Pipeline et Cartograp.pdf

<file://file-Wq7nEwUX7m8MFTB1pnCVXa>

[\[2\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Il%20faut%20prendre%20en%20compte,log%20pour%20pour%20la%20tra%C3%A7abilit%C3%A9)
[\[21\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=La%20colonne%20ID%20n%27est%20pas,Chronogramme%20et%20l%27id%20de%20l%27injecte)
[\[50\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Pour%20les%20premi%C3%A8res%20%C3%A9tapes%20on,tableau%20comme%20c%27est%20tr%C3%A8s%20h%C3%A9t%C3%A9rog%C3%A8ne)
[\[51\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Pour%20les%20IA%20on%20utilisera,5)
[\[52\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Pour%20stocker%20les%20bases%20de,enfin%20migrer%20tout%20%C3%A7a%20versPostgreSQL)
[\[53\]](file://file-5Ewi9xpmF3uCGtRJsv2Bw2#:~:text=Et%20de%20plus%20je%20souhaite,fichier%20je%20fais%20le%20journal)
squelette projet.docx

<file://file-5Ewi9xpmF3uCGtRJsv2Bw2>

# 6. Stratégie de tests unitaires et de validation automatisée

Objectif : fournir une batterie de tests reproductibles couvrant chaque
module du pipeline, garantir l'absence de régressions, et documenter un
mode opératoire standard (CI/CD) pour l'équipe.

Hypothèses : l'implémentation suit l'arborescence décrite (src/ avec les
modules main.py, form_handler.py, excel_parser.py, data_cleaner.py,
standardizer.py, enricher.py, db_utils.py, logger.py,
correction_tool.py) et utilise pandas/openpyxl/SQLite + appels LLM
encapsulés.

## 6.1 Outils et principes

• Cadre de tests : pytest

• Mesure de couverture : coverage.py (objectif ≥ 90% lignes, ≥ 80%
branches)

• Mocks : monkeypatch/pytest-mock pour isoler les E/S (fichiers, réseau,
SQLite) et l'API LLM

• Tests rapides, déterministes et parallélisables (pas d'accès réseau
réel ; bases SQLite en mémoire)

• Données de test minimales, versionnées aux côtés du code (fixtures
Excel synthétiques)

## 6.2 Arborescence des tests

chronogram_pipeline/\
└── tests/\
├── conftest.py\
├── factories.py\
├── fixtures/\
│ ├── excels/\
│ │ ├── chrono_basique.xlsx\
│ │ ├── chrono_avec_phases.xlsx\
│ │ ├── chrono_entetes_variants.xlsx\
│ │ └── chrono_cells_fusionnees.xlsx\
│ ├── mapping_headers.csv\
│ ├── mapping_values.csv\
│ └── schema_definition.yaml\
├── test_main.py\
├── test_form_handler.py\
├── test_excel_parser.py\
├── test_data_cleaner.py\
├── test_standardizer_headers.py\
├── test_standardizer_values.py\
├── test_enricher.py\
├── test_db_utils.py\
├── test_logger.py\
└── test_correction_tool.py

## 6.3 Fixtures et isolation

• conftest.py : crée des dossiers temporaires (tmp_path), configure
l'environnement et un logger silencieux.

• Bases : utiliser sqlite3.connect(\':memory:\') ou un fichier
temporaire par test, avec rollback et fermeture propres.

• LLM : fournir des stubs pour gpt_suggest_header/gpt_suggest_value
renvoyant des réponses déterministes.

• Fichiers Excel : petites matrices synthétiques couvrant les cas
limites (lignes vides, entêtes variables, fusions).

• Temps : si nécessaire, freezegun pour figer l'horodatage des logs.

## 6.4 Cas de test par module

A\) excel_parser.py

1\. detect_main_sheet : sélectionne la feuille la plus dense ; tie-break
sur mot-clé « Chronogramme ».

2\. find_data_table : localise la ligne d'en-tête et la fin du tableau ;
ignore les blocs « Phase X » optionnels.

3\. extract_data : ne lit que la plage utile ; vérifie les types de
colonnes attendus.

B\) data_cleaner.py

1\. unmerge_cells : propage correctement les valeurs
verticales/horizontales (NaN remplacés).

2\. drop_empty_rows/cols : supprime les lignes/colonnes vides ; compte
exact des suppressions.

3\. règles spécifiques : suppression des lignes « Phase » ou « Total »
si configuré.

C\) standardizer.py -- En-têtes

1\. Mapping par dictionnaire : renommage exact et stable ; colonnes
inconnues marquées « ignorées ».

2\. Fallback LLM : stub renvoyant un nom du schéma ; rejet si hors
schéma.

3\. Traçabilité : écriture d'une ligne dans mappings_log (ou structure
en mémoire) avec source=règle/IA.

D\) standardizer.py -- Valeurs

1\. Synonymes connus : « Mail », « Courriel », « Email » → « Email ».

2\. Nouvelle valeur : stub LLM propose une valeur standard autorisée ;
ajout au mapping in-memory.

3\. Idempotence : rejouer l'uniformisation n'altère plus les valeurs
standardisées.

E\) enricher.py

1\. Ajout des colonnes (chronogramme_id, établissement, type, etc.).

2\. id_inject : respecte l'ID existant ; sinon génère 1..N en conservant
l'ordre.

3\. Réordonnancement final des colonnes selon le schéma.

F\) db_utils.py

1\. init_tables : crée le schéma attendu (Chronogrammes, Injects).

2\. insert_chronogram : retourne un ID ; champs normalisés/trim.

3\. insert_injects : transaction englobante ; contrainte d'unicité
(id_chronogramme, id_inject) ; rollback en cas d'échec.

G\) logger.py

1\. Format attendu (timestamp, niveau, module) ; écrit dans
data/control/run\_\<timestamp\>.log.

2\. Niveaux : DEBUG en dev, INFO/ERROR en prod ; tests vérifient la
présence de messages clés.

H\) correction_tool.py

1\. Lecture des mappings modifiés ; génération d'UPDATE ciblés en base.

2\. Journalisation des corrections appliquées.

3\. Tests sur un échantillon (avant/après) garantissant la convergence.

I\) main.py (intégration)

1\. Orchestration « happy path » de bout en bout (utilisant de petites
fixtures).

2\. Gestion d'erreur : injection d'une panne contrôlée (ex. conflit
d'unicité) → rollback total, aucun artefact persistant (fichiers de
mapping non écrits prématurément).

## 6.5 Données de test minimales

• chrono_basique.xlsx : petit tableau propre (5--10 lignes).

• chrono_avec_phases.xlsx : lignes « Phase » intercalées ; vérifie
l'exclusion/prise en compte paramétrée.

• chrono_entetes_variants.xlsx : variantes d'intitulés pour tester le
mapping en-têtes.

• chrono_cells_fusionnees.xlsx : fusions verticales/horizontales sur
quelques colonnes.

## 6.6 Exemples de tests (extraits)

\# tests/test_standardizer_headers.py\
def test_standardize_headers_uses_dictionary_first(monkeypatch,
tmp_path):\
from src.standardizer import standardize_headers\
headers = \[\"Descriptif\", \"Destinataires potentiels\",
\"Modalité\"\]\
schema = \[\"Contenu\", \"Destinataire\", \"Modalité\",
\"Horodatage\"\]\
\# Stub LLM pour toute valeur inconnue\
def fake_gpt(header, allowed):\
return \"Destinataire\" if \"Destinataires\" in header else
\"Modalité\"\
mapping_dict = {\"Descriptif\": \"Contenu\"}\
out = standardize_headers(headers_list=headers,
mapping_dict=mapping_dict, allowed_schema=schema,
gpt_suggest_header=fake_gpt)\
assert out == \[\"Contenu\", \"Destinataire\", \"Modalité\"\]\
\
\# tests/test_db_utils.py\
def test_insert_injects_transaction_rollback(tmp_path):\
from src import db_utils\
conn = db_utils.init_in_memory() \# helper qui active PRAGMA
foreign_keys=ON\
db_utils.init_tables(conn)\
chrono_id = db_utils.insert_chronogram(conn, {\"nom_chronogramme\":
\"Test\"})\
rows = \[\
{\"id_chronogramme\": chrono_id, \"id_inject\": 1, \"description\":
\"A\"},\
{\"id_chronogramme\": chrono_id, \"id_inject\": 1, \"description\":
\"Conflit\"}, \# viole l\'unicité\
\]\
try:\
db_utils.insert_injects(conn, rows)\
except Exception:\
pass\
\# La table doit rester vide si tout est rollbacké\
assert db_utils.count_injects(conn, chrono_id) == 0

## 6.7 Mesure de couverture et commandes

\# Installation (incluant dépendances de test)\
pip install -r requirements.txt\
pip install pytest coverage pytest-mock freezegun\
\
\# Lancer les tests\
pytest -q\
\
\# Couverture\
coverage run -m pytest\
coverage html \# rapport dans htmlcov/index.html

## 6.8 Intégration continue (exemple GitHub Actions)

name: tests\
on: \[push, pull_request\]\
jobs:\
pytest:\
runs-on: ubuntu-latest\
steps:\
- uses: actions/checkout@v4\
- uses: actions/setup-python@v5\
with:\
python-version: \'3.11\'\
- run: pip install -r requirements.txt\
- run: pip install pytest coverage pytest-mock freezegun\
- run: pytest -q\
- run: coverage run -m pytest && coverage xml\
- uses: codecov/codecov-action@v4\
if: always()

## 6.9 Mise à jour de l'arborescence (ajout des tests)

chronogram_pipeline/\
├── README.md\
├── requirements.txt\
├── chronogram_pipeline/config/\
├── data/\
├── output/\
├── src/\
└── tests/ \# NOUVEAU : suite de tests pytest\
├── conftest.py\
├── fixtures/\
└── (\... fichiers de tests \...)
