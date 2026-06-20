# Panier repas — Google Form scripted

Crée un Google Form **« Panier repas »** optimisé pour la saisie mobile rapide,
et lie ses réponses au Sheet existant
`1SqykyaboMvX3zBx8YEH5COceqLjHWem7CvHZlqbwTvQ`.

L'API REST Forms gère la création du formulaire et des questions ; elle ne sait
**pas** définir la feuille de destination, ni les réglages « Modifier après
l'envoi » / « Collecter les e-mails ». On utilise donc :

1. `create_form.py` (Python + Forms REST API) pour créer le form et les
   questions.
2. `apps_script/linkAndConfigure.gs` (Apps Script, via clasp) pour la liaison
   au Sheet **et** les 2 réglages manquants. Fallback manuel documenté plus bas
   si tu ne veux pas installer clasp.

## 1. Setup GCP (à faire une fois, ~5 min)

1. Va sur https://console.cloud.google.com/.
2. Crée un projet (ou réutilises-en un) : barre du haut → **Sélectionner un
   projet** → **Nouveau projet** → nom au choix (ex. `panier-repas`).
3. Active l'API Forms :
   - https://console.cloud.google.com/apis/library/forms.googleapis.com → bouton
     **Activer**.
4. Configure l'écran de consentement OAuth :
   - **APIs & Services** → **OAuth consent screen**.
   - User type : **External** (tu es seul utilisateur, c'est ok).
   - Remplis le strict minimum (nom de l'app, ton e-mail). **Save and continue**
     jusqu'à la fin.
   - Onglet **Test users** → ajoute ton compte (`simon.dolle@gmail.com`).
     Tant que l'app est en *Testing*, seuls les test users peuvent s'authentifier.
5. Crée le client OAuth :
   - **APIs & Services** → **Credentials** → **Create credentials** →
     **OAuth client ID**.
   - Application type : **Desktop app**.
   - Télécharge le JSON, renomme-le en `credentials.json`, dépose-le dans ce
     dossier (`panier_repas/credentials.json`). Il est gitignoré.

## 2. Création du form

```bash
cd panier_repas
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python create_form.py
```

Au premier lancement, un navigateur s'ouvre pour le consentement OAuth (compte
Google de destination = celui qui possèdera le form et le Sheet). Token mis en
cache dans `token.json` (gitignoré).

Sortie : `form_info.json` + un récap imprimé avec :

- l'**URL de réponse** (à ajouter à l'écran d'accueil mobile),
- l'**URL d'édition**,
- le **Form ID**.

## 3. Liaison au Sheet + réglages

### Option A — Apps Script via clasp (recommandé)

Installe clasp si ce n'est pas fait :

```bash
npm install -g @google/clasp
clasp login
```

`clasp login` ouvre un navigateur ; choisis le **même compte Google** que pour
le form. Puis :

```bash
cd panier_repas/apps_script
# Édite linkAndConfigure.gs et remplace REPLACE_WITH_FORM_ID par le formId
clasp create --type standalone --title "Panier repas - link"
clasp push -f
clasp run linkAndConfigure
```

`clasp create` génère un `.clasp.json` local (gitignoré). À la première
exécution, `clasp run` peut demander d'activer l'API Apps Script
(https://script.google.com/home/usersettings → **Apps Script API** ON) et de
réautoriser. Logs : `clasp logs` ou Cloud Logging.

### Option B — manuel (6 clics)

Si tu préfères ne pas installer clasp :

1. Ouvre l'URL d'édition imprimée par `create_form.py`.
2. Onglet **Réponses**.
3. Clique l'**icône verte Sheets** en haut à droite.
4. **Sélectionner une feuille de calcul existante** → choisis le Sheet
   `1SqykyaboMvX3zBx8YEH5COceqLjHWem7CvHZlqbwTvQ`.
5. Roue dentée ⚙ (paramètres du form) → onglet **Général** → **décoche**
   « Collecter les adresses e-mail ».
6. Toujours dans **Général** → **coche** « Les répondants peuvent : modifier
   les réponses après l'envoi ». Save.

## 4. Vérification que les réponses arrivent dans le Sheet

1. Ouvre l'URL de réponse, envoie une réponse test.
2. Ouvre le Sheet — un nouvel onglet `Réponses au formulaire 1` (ou similaire)
   a été créé, avec une ligne contenant horodatage + tes réponses.
3. Supprime la ligne de test si tu veux.

## Réutilisation / extension

- Pour ajouter / modifier des questions plus tard : édite `CHOICE_QUESTIONS` /
  `TEXT_QUESTION_TITLE` dans `create_form.py` et relance. Note : le script
  **crée un nouveau form** à chaque lancement. Pour patcher un form existant,
  il faudrait utiliser `forms().batchUpdate()` avec `updateItem` /
  `deleteItem` ciblés sur le `formId` existant.
- Token expiré : supprime `token.json`, relance, refais le consentement.

## Fichiers

```
panier_repas/
├── README.md                       # ce fichier
├── requirements.txt
├── create_form.py                  # API REST Forms : crée form + questions
├── apps_script/
│   ├── appsscript.json             # manifest Apps Script (scopes)
│   └── linkAndConfigure.gs         # liaison Sheet + 2 settings
├── .gitignore
└── (au runtime, gitignorés)
    ├── credentials.json            # OAuth client secret
    ├── token.json                  # cache OAuth user
    └── form_info.json              # formId + URLs après création
```
