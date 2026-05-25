# 📻 Radio Sources de Vie Chrétienne — Guide de démarrage

## Structure des fichiers

```
Radio-Sources-de-Vie/
├── index.html              ← Site principal (déjà sur GitHub Pages)
├── weather.json            ← Météo du jour (généré par fetch_weather.py)
├── news_latest.json        ← Nouvelles récentes (généré par fetch_news.py)
│
├── fetch_weather.py        ← Script météo
├── fetch_news.py           ← Script nouvelles RSS
├── generate_content.py     ← Script prière/sermon/témoignage (Anthropic API)
├── auto_push.py            ← Script maître (tout-en-un + git push)
│
└── content/
    ├── prayers/            ← prière du jour: 2025-01-24.json
    ├── sermons/            ← sermon du jour: 2025-01-24.json
    ├── testimonies/        ← témoignage du jour: 2025-01-24.json
    └── news/               ← archives nouvelles par date
```

---

## Installation (une seule fois)

```bash
# Dans Git Bash, depuis C:\Users\avena\Desktop\radio sources De Vie
pip install requests feedparser anthropic
```

Obtenir les clés API:
- **OpenWeatherMap** (gratuit): https://openweathermap.org/api → "Get API key"
- **Anthropic Claude** (payant): https://console.anthropic.com → API Keys

---

## Utilisation quotidienne

### Option A — Script maître (recommandé)
```bash
python auto_push.py \
  --owm-key VOTRE_CLE_OPENWEATHERMAP \
  --anthropic-key VOTRE_CLE_ANTHROPIC
```

### Option B — Scripts individuels
```bash
# Météo seulement
python fetch_weather.py --api-key VOTRE_CLE_OWM

# Nouvelles seulement
python fetch_news.py

# Contenu spirituel seulement
python generate_content.py --api-key VOTRE_CLE_ANTHROPIC --type all
```

---

## Planification automatique (Windows)

Ouvrir "Planificateur de tâches" → Créer une tâche de base:

| Heure | Commande |
|-------|----------|
| 06:00 | `python auto_push.py --owm-key KEY --anthropic-key KEY` |
| 12:00 | `python auto_push.py --owm-key KEY --skip-content` |
| 18:00 | `python auto_push.py --owm-key KEY --skip-content` |

---

## Format JSON du contenu quotidien

### Prière / Sermon / Témoignage
```json
{
  "title": "Titre",
  "date": "2025-01-24",
  "verse": "Car Dieu a tant aimé le monde...",
  "reference": "Jean 3:16",
  "content": "Texte complet..."
}
```

### Météo (weather.json)
```json
{
  "updated": "2025-01-24T12:00:00Z",
  "ottawa": { "temp": -5, "description": "Neige légère", "humidity": 80 },
  "pap":    { "temp": 32, "description": "Ensoleillé",   "humidity": 65 }
}
```

---

## Dépannage

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError` | `pip install requests feedparser anthropic` |
| Météo ne charge pas | Vérifier la clé OWM sur openweathermap.org |
| Git push refusé | Configurer: `git config user.email "vous@email.com"` |
| JSON invalide | Relancer generate_content.py (retry automatique) |

---

*"Je suis le chemin, la vérité et la vie." — Jean 14:6* 🙏
