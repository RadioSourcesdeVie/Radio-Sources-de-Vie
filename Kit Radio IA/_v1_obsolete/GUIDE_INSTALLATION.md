# Kit Radio IA — Guide d'installation

Ce kit génère automatiquement, chaque jour, le contenu audio de votre radio
(bulletins d'actualités, prières, sermons, témoignages, sweepers) grâce à
l'intelligence artificielle, et l'intègre à RadioDJ pour une diffusion
100% automatisée.

Temps d'installation estimé : 45 à 90 minutes la première fois.

---

## 1. Prérequis

- Windows 10 ou 11
- [RadioDJ](https://www.radiodj.ro/) déjà installé et fonctionnel, avec une
  bibliothèque musicale importée
- [Python 3.11 ou 3.12](https://www.python.org/downloads/) installé
  (cocher "Add python.exe to PATH" pendant l'installation)
- Une connexion Internet stable sur le serveur/ordinateur qui diffuse

## 2. Obtenir votre clé API Gemini (gratuite)

1. Allez sur https://aistudio.google.com/apikey
2. Connectez-vous avec un compte Google
3. Cliquez sur "Create API key"
4. Copiez la clé (elle commence par `AIza...`)

Cette clé sert à générer les textes et les voix. Le niveau gratuit de
Google Gemini couvre largement l'usage d'une petite station.

## 3. Installer les dépendances Python

1. Copiez le dossier `Kit Radio IA` à l'endroit où vous voulez qu'il vive
   en permanence (ex: `C:\RadioIA\`)
2. Ouvrez une invite de commandes dans ce dossier (clic droit > "Ouvrir dans
   le terminal")
3. Installez les dépendances :

   ```
   pip install -r requirements.txt
   pip install google-genai
   ```

## 4. Personnaliser `config.py`

Ouvrez `config.py` avec le Bloc-notes ou VS Code. C'est le SEUL fichier à
modifier. Remplissez chaque section :

1. **Identité** : nom de la station, slogan, langue
2. **Géographie** : ville principale (météo + actus locales), ville
   diaspora optionnelle, nom du pays/de la communauté
3. **Sources d'actualités** : ajoutez vos flux RSS (locaux, internationaux,
   chrétiens). Testez chaque lien dans un navigateur avant de l'ajouter —
   il doit afficher du XML
4. **Clé API Gemini** : collez la clé obtenue à l'étape 2
5. **Horaire** : ajustez les heures de diffusion de chaque segment, ou
   retirez les segments non désirés
6. **RadioDJ** : nom de la base de données, mot de passe MySQL, port REST
   (voir étape 5 ci-dessous pour les trouver)

## 5. Retrouver vos informations RadioDJ

Dans RadioDJ :

1. **Base de données** : Options > Database. Le nom de la base ressemble à
   `radiodj2050VotreStation`. Notez host, port, utilisateur, mot de passe.
2. **API REST** : Options > REST API. Notez le port (par défaut 8080) et le
   mot de passe REST.
3. **Dossiers de catégories** : dans l'onglet Library de RadioDJ, notez le
   chemin des catégories où les fichiers générés doivent atterrir (ex:
   "Nouvelles/Meteo"). Créez ces catégories si elles n'existent pas encore,
   et ajoutez-les comme Events programmés dans RadioDJ (Tools > Event
   Scheduler) pour qu'AutoDJ les joue automatiquement.

Reportez toutes ces valeurs dans `config.py` (section 6).

## 6. Premier test manuel

Avant d'automatiser, testez chaque segment un par un :

```
python bulletin_matin.py
python priere_matin.py
python sermon_matin.py
python temoignage.py
python generate_sweepers.py
```

Chaque script affiche sa progression et enregistre un fichier `.wav` (ou
`.mp3` pour les sweepers) dans un sous-dossier (`nouvelles/`, `priere/`,
`sermon/`, `temoignage/`). Écoutez-les pour valider le ton et la qualité
avant de passer à l'automatisation.

## 7. Synchroniser avec RadioDJ

```
python sync_radiodj.py
```

Ce script copie le dernier audio généré de chaque segment vers les dossiers
RadioDJ définis dans `config.py`. Lancez-le manuellement une fois pour
vérifier que les fichiers apparaissent bien dans votre bibliothèque RadioDJ
(faites un scan de la bibliothèque dans RadioDJ si besoin).

## 8. Automatiser avec le Planificateur de tâches Windows

```
installer_taches.bat
```

(clic droit > "Exécuter en tant qu'administrateur" pour une installation au
niveau SYSTEM — sinon les tâches sont créées pour l'utilisateur courant,
ce qui fonctionne aussi tant que la session reste ouverte).

Ce script crée automatiquement une tâche planifiée Windows par segment,
aux heures définies dans `config.py`. Ajoutez ensuite une tâche planifiée
supplémentaire pour `run_sync_radiodj.bat`, quelques minutes après chaque
segment, afin que le fichier généré soit copié vers RadioDJ automatiquement.

Pour les sweepers, planifiez `run_sweepers.bat` une fois par semaine (lot
de 3) ou une fois par mois (lot de 10+, ajustable dans `config.py`).

## 9. Demandes d'auditeurs (optionnel)

`radiodj_request.py` permet de chercher une chanson dans votre bibliothèque
RadioDJ et de l'ajouter à la file de lecture — utile pour un chatbot de
demandes ou une interface web que vous branchez par-dessus.

## 10. Dépannage

- **"config.py incomplet"** : la clé Gemini n'a pas été collée dans
  `config.py`.
- **Aucun article récupéré** : vérifiez vos flux RSS un par un dans un
  navigateur.
- **Erreur de connexion RadioDJ** : vérifiez host/port/utilisateur/mot de
  passe dans `config.py` (section 6), et que le service MySQL de RadioDJ
  tourne.
- **Tâche planifiée qui ne se déclenche pas** : relancez
  `installer_taches.bat` en administrateur, ou vérifiez dans le
  Planificateur de tâches Windows (`taskschd.msc`) que la tâche existe et
  est activée.

---

Besoin d'aide pour l'installation ou la personnalisation ? Contactez le
support inclus avec votre achat.
