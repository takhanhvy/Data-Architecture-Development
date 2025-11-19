# Jeux de données front-end

Le dashboard tente d'abord de charger `./data/paris-arrondissements.geojson`.  
Si ce fichier n'existe pas, il bascule vers les sources publiques définies dans `app.js` (Open Data Paris et un miroir GitHub).

Pour un usage hors-ligne, téléchargez le GeoJSON officiel depuis https://opendata.paris.fr/explore/dataset/arrondissements/ et enregistrez-le sous ce dossier avec le nom `paris-arrondissements.geojson`.
