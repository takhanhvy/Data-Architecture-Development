# DVF Backend & Frontend Quickstart

## Backend (Flask)

1. Créez un environnement virtuel (facultatif) et installez les dépendances spécifiques :
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
2. Lancez l'API :
   ```bash
   flask --app backend.app --debug run
   ```
   (ou `python -m backend.app`). Le serveur écoute par défaut sur `http://127.0.0.1:5000`.

### Endpoints disponibles

| Méthode | Route                                         | Description                                                                                      |
|---------|-----------------------------------------------|--------------------------------------------------------------------------------------------------|
| GET     | `/api/health`                                 | Vérifie que l'API répond.                                                                        |
| GET     | `/api/dvf/years`                              | Liste des années pour lesquelles la couche gold contient des agrégats.                           |
| GET     | `/api/dvf/arrondissements?year=2024`          | Agrégation prix médian et volume de ventes par arrondissement (filtrage par année/`type_local`). |
| GET     | `/api/dvf/arrondissements/<code>/timeseries`  | Séries temporelles pour un arrondissement donné (ex : `code=75101`).                            |
| POST    | `/api/cache/reload`                           | Recharge le CSV `data/gold_layer/agg_dvf_data.csv` sans redémarrer le serveur.                   |

Les payloads retournent des structures prêtes à être utilisées dans des graphiques (prix médian au m², nb de transactions, libellés arrondis, etc.).

## Frontend (dashboard statique Leaflet)

1. Démarrez l'API Flask (voir ci-dessus).
2. Servez le dossier `frontend/` avec n'importe quel serveur statique, par exemple :
   ```bash
   cd frontend
   python -m http.server 4173
   ```
   puis ouvrez `http://127.0.0.1:4173`.

### Fonctionnalités clés

- Carte choropleth des 20 arrondissements parisiens (Leaflet + GeoJSON).
- Sélecteur d'année synchronisé avec l'endpoint `/api/dvf/arrondissements`.
- Infobulles au survol affichant prix médian au m² et nombre de ventes.
- Échelle de couleurs dynamique recalculée à chaque changement d'année.

### Données géographiques

- Le dashboard tente d'abord de charger `frontend/data/paris-arrondissements.geojson`.
- À défaut, deux sources publiques sont utilisées automatiquement (Open Data Paris et un miroir GitHub).
- Pour un usage hors-ligne, téléchargez le GeoJSON officiel et placez-le dans `frontend/data/paris-arrondissements.geojson`.
- Si aucune source n'est disponible, une grille simplifiée est générée pour visualiser malgré tout la choropleth (utile pour maquettage).

### Astuces supplémentaires

- Les endpoints supplémentaires (`timeseries`) peuvent alimenter des graphiques complémentaires (sparkline, comparatifs, etc.).
- Ajoutez un reverse proxy (ex: `flask run --host 0.0.0.0`) si vous devez servir l'API et le front depuis un même domaine pour éviter le CORS.
- Les couleurs sont générées à partir des min/max annuels. Pour des seuils fixes (par ex. classification d'échelle), adaptez `buildColorScale` dans `frontend/app.js`.
