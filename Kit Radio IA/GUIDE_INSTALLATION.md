# Kit Radio IA — Guide d'installation

Ce kit génère automatiquement, chaque jour, le contenu audio de votre radio
(météo, actualités, prières, sermon, témoignages, journal du soir, sweepers)
grâce à l'IA, et l'intègre à RadioDJ pour une diffusion 100% automatisée.

Textes générés par **Claude** (Anthropic). Voix au choix : **Edge TTS**
(Microsoft, gratuit — recommandé), **ElevenLabs** (payant, qualité premium)
ou **Gemini** (Google, payant au-delà du quota gratuit). Fonctionne dans
toute langue supportée par le fournisseur de voix choisi.

Temps d'installation estimé : 45 à 90 minutes la première fois.

---

## 1. Prérequis

- Windows 10 ou 11
- [RadioDJ](https://www.radiodj.ro/) déjà installé et fonctionnel, avec une
  bibliothèque musicale importée
- [Python 3.11 ou 3.12](https://www.python.org/downloads/) installé
  (cocher "Add python.exe to PATH" pendant l'installation)
- Une connexion Internet stable sur l'ordinateur qui diffuse

## 2. Obtenir vos clés API

1. **Claude (obligatoire, génération de texte)** : créez une clé sur
   https://console.anthropic.com/settings/keys. Coût très faible (modèle
   Haiku) — quelques centimes par jour pour une station.
2. **OpenWeatherMap (obligatoire, météo)** : créez une clé gratuite sur
   https://openweathermap.org/api
3. **Voix — un seul choix nécessaire** :
   - **Edge TTS** : rien à faire, c'est gratuit et déjà inclus.
   - **ElevenLabs** (optionnel, payant) : clé sur
     https://elevenlabs.io/app/settings/api-keys
   - **Gemini** (optionnel, payant) : clé sur https://aistudio.google.com/apikey

## 3. Installer les dépendances Python

1. Copiez le dossier `Kit Radio IA` à l'endroit où il vivra en permanence
   (ex: `C:\RadioIA\`)
2. Ouvrez une invite de commandes dans ce dossier (clic droit > "Ouvrir dans
   le terminal")
3. Installez les dépendances :

   ```
   pip install -r requirements.txt
   ```

   Si vous choisissez ElevenLabs ou Gemini comme voix, aucune dépendance
   supplémentaire n'est nécessaire (ElevenLabs utilise `requests`, déjà
   installé) — sauf pour Gemini : `pip install google-genai`

## 4. Personnaliser `config.py`

Ouvrez `config.py` avec le Bloc-notes ou VS Code. C'est le SEUL fichier à
modifier. Remplissez chaque section, dans l'ordre :

1. **Identité** : nom de la station, langue, communauté/pays
2. **Géographie** : ville principale (format `"Ville,CODE_PAYS"` — voir
   codes ISO pays), ville diaspora optionnelle
3. **Clé Claude** (`ANTHROPIC_API_KEY`)
4. **Clé météo** (`OWM_API_KEY`)
5. **Moteur de voix** : `TTS_PROVIDER = "edge"` (par défaut, gratuit),
   `"elevenlabs"` ou `"gemini"`. Complétez la clé et les voix par rôle
   correspondantes uniquement pour le fournisseur choisi. Pour explorer
   toutes les voix Edge TTS disponibles (100+ langues) :
   `pip install edge-tts` puis `edge-tts --list-voices`
6. **Prières par jour** (`PRIERE_MOMENTS`) : listez autant de moments que
   vous voulez, ex: `["matin", "soir"]` ou `["matin", "midi", "soir"]`
7. **Sources d'actualités** : ajoutez vos flux RSS par catégorie. Testez
   chaque lien dans un navigateur avant de l'ajouter — il doit afficher du XML
8. **Horaire** : ajustez les heures des scripts orchestrateurs
9. **RadioDJ** : base de données, mot de passe MySQL, port REST, dossiers
   (voir étape 5 ci-dessous)

## 5. Retrouver vos informations RadioDJ

Dans RadioDJ :

1. **Base de données** : Options > Database. Notez host, port, nom de la
   base, utilisateur, mot de passe.
2. **API REST** : Options > REST API. Notez le port (8080 par défaut) et le
   mot de passe REST.
3. **Dossiers de catégories** : dans l'onglet Library, créez les catégories
   nécessaires (météo, prières, sermon, témoignage, résumés, sweepers) et
   ajoutez-les comme Events programmés (Tools > Event Scheduler) pour
   qu'AutoDJ les diffuse aux heures voulues.

Reportez ces valeurs dans `config.py` (section RadioDJ).

## 6. Premier test manuel

Testez chaque étape avant d'automatiser :

```
python fetch_weather.py
python fetch_news.py
python generate_content.py
python generate_sermon.py
python generate_daily_audio.py
python generate_resumes.py
python generate_bulletin_soir.py
python generate_sweepers.py
```

Chaque script affiche sa progression. Écoutez les fichiers audio produits
(dans `audio/`) pour valider ton et qualité.

## 7. Synchroniser avec RadioDJ

```
python sync_radiodj.py
```

Copie les derniers audios du jour vers les dossiers RadioDJ configurés
(les sweepers sont copiés directement par `generate_sweepers.py`). Faites un
scan de bibliothèque dans RadioDJ pour vérifier que les fichiers apparaissent.

## 8. Automatiser avec le Planificateur de tâches Windows

```
installer_taches.bat
```

(clic droit > "Exécuter en tant qu'administrateur" pour une installation
SYSTEM — sinon les tâches tournent pour l'utilisateur courant, ce qui
fonctionne aussi tant que la session reste ouverte).

Ce script crée une tâche par entrée de `config.HORAIRE`, chacune lançant un
orchestrateur (`run_meteo.py`, `run_spirituel.py`, `run_news.py`,
`run_bulletin_soir.py`, `run_sweepers.py`) qui génère le contenu **et**
synchronise RadioDJ automatiquement — un seul aller-retour au Planificateur
de tâches suffit par segment.

## 9. Demandes d'auditeurs (optionnel)

`radiodj_request.py` cherche une chanson dans votre bibliothèque RadioDJ et
l'ajoute à la file de lecture — utile pour un chatbot de demandes ou une
interface web branchée par-dessus.

## 10. Changer de fournisseur de voix plus tard

Modifiez simplement `TTS_PROVIDER` dans `config.py` et complétez la clé/les
voix du nouveau fournisseur — aucun autre fichier à toucher. Les prochains
audios générés utiliseront automatiquement la nouvelle voix (les anciens
fichiers déjà générés ne sont pas régénérés).

## 11. Dépannage

- **"config.py incomplet"** : une clé obligatoire n'a pas été remplie
  (Claude, ou la clé du fournisseur de voix choisi).
- **Aucun article récupéré** : vérifiez vos flux RSS un par un dans un
  navigateur.
- **Erreur RadioDJ** : vérifiez host/port/utilisateur/mot de passe dans
  `config.py`, et que le service MySQL de RadioDJ tourne.
- **Tâche planifiée qui ne se déclenche pas** : relancez
  `installer_taches.bat` en administrateur, ou vérifiez dans le
  Planificateur de tâches Windows (`taskschd.msc`).
- **Fichier audio illisible dans RadioDJ** : si vous utilisez Gemini comme
  voix, les fichiers sont en `.wav` (pas `.mp3`) — assurez-vous que la
  catégorie RadioDJ accepte le WAV (c'est le cas par défaut).

---

Besoin d'aide pour l'installation ou la personnalisation ? Contactez le
support inclus avec votre achat.
