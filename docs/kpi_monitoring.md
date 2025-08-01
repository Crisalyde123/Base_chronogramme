# KPI de couverture du pipeline

Ce document décrit les indicateurs utilisés pour suivre la qualité des traitements et les seuils d'alerte associés.

## Définitions

Soit `N` le nombre total d'éléments considérés pour un traitement (en‑têtes ou valeurs). Pour un identifiant de chronogramme donné :

- **Taux de standardisation automatique** :
  \[\text{auto\_rate} = \frac{N_{\text{règle}}}{N}\]
  où `N_{règle}` est le nombre d'éléments standardisés par les règles locales.
- **Taux de recours à l'IA** :
  \[\text{ia\_rate} = \frac{N_{\text{IA}}}{N}\]
  où `N_{IA}` est le nombre d'éléments standardisés grâce à une suggestion IA.
- **Taux non résolu** :
  \[\text{unresolved\_rate} = \frac{N_{\text{vide}}}{N}\]
  où `N_{vide}` est le nombre d'éléments n'ayant reçu aucune correspondance.
- **Complétude des injects** :
  \[\text{completude} = \frac{\text{nombre de cellules renseignées}}{\text{nombre total de cellules attendues}}\]
  Le calcul exclut la colonne technique `id_chronogramme`.

## Seuils d'alerte

- **Alerte jaune** si l'un des critères suivants est dépassé :
  - `ia_rate` > 40 %
  - `unresolved_rate` > 10 %
  - `completude` < 90 %
- **Alerte rouge** si l'un des critères suivants est dépassé :
  - `ia_rate` > 60 %
  - `unresolved_rate` > 20 %
  - `completude` < 70 %

Les seuils sont ajustables selon la qualité réelle des fichiers analysés.
