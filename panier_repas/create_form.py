#!/usr/bin/env python3
"""Create the 'Panier repas' Google Form via the Forms REST API.

Usage:
    python create_form.py

Prerequisites:
    - credentials.json (OAuth client secret) sitting next to this file
    - pip install -r requirements.txt
    See README.md for the GCP setup walkthrough.

The script writes form_info.json with the form ID and URLs, then prints
the next steps (linking to the destination Sheet + a couple of settings
that the REST API does not expose).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/forms.body"]

SCRIPT_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"
OUTPUT_FILE = SCRIPT_DIR / "form_info.json"

FORM_TITLE = "Panier repas"

# Each tuple: (title, type, options, allow_other)
CHOICE_QUESTIONS = [
    (
        "Féculent",
        "RADIO",
        ["riz", "coquillettes", "spaghettis", "semoule", "pommes de terre", "Aucun"],
        True,
    ),
    (
        "Protéine",
        "RADIO",
        ["crevettes", "filet de sole", "jambon", "nuggets", "œuf", "poulet", "Aucun"],
        True,
    ),
    (
        "Légume",
        "RADIO",
        ["tomates cerises", "carottes râpées", "melon", "pastèque", "concombre", "Aucun"],
        True,
    ),
    (
        "Fruit",
        "CHECKBOX",
        ["fraises", "cerises", "framboises", "myrtilles", "mûres", "pastèque"],
        True,
    ),
    (
        "Goûter",
        "RADIO",
        ["madeleine", "nounours chocolat", "Aucun"],
        True,
    ),
    (
        "Pain",
        "RADIO",
        ["pain de mie", "Aucun"],
        False,
    ),
    (
        "Appétit",
        "RADIO",
        ["Tout mangé", "Bien mangé", "Moitié", "Peu mangé"],
        False,
    ),
]

TEXT_QUESTION_TITLE = "Restes (quoi)"
TEXT_QUESTION_DESCRIPTION = 'Noms d\'aliments laissés, ex. "melon, pastèque"'


def get_credentials() -> Credentials:
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
        return creds
    if not CREDENTIALS_FILE.exists():
        sys.exit(
            f"Missing {CREDENTIALS_FILE}. Download an OAuth client secret JSON "
            "from the Google Cloud Console and save it there. See README.md."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    return creds


def build_choice_item(title: str, qtype: str, options: list[str], allow_other: bool) -> dict:
    opts: list[dict] = [{"value": opt} for opt in options]
    if allow_other:
        opts.append({"isOther": True})
    return {
        "title": title,
        "questionItem": {
            "question": {
                "required": False,
                "choiceQuestion": {
                    "type": qtype,
                    "options": opts,
                    "shuffle": False,
                },
            }
        },
    }


def build_text_item(title: str, description: str) -> dict:
    return {
        "title": title,
        "description": description,
        "questionItem": {
            "question": {
                "required": False,
                "textQuestion": {"paragraph": False},
            }
        },
    }


def main() -> None:
    creds = get_credentials()
    service = build("forms", "v1", credentials=creds)

    # forms.create() only accepts the `info` field; items must come via batchUpdate.
    form = service.forms().create(body={"info": {"title": FORM_TITLE}}).execute()
    form_id = form["formId"]
    print(f"Form created: {form_id}")

    requests_list: list[dict] = []
    for index, (title, qtype, options, allow_other) in enumerate(CHOICE_QUESTIONS):
        requests_list.append(
            {
                "createItem": {
                    "item": build_choice_item(title, qtype, options, allow_other),
                    "location": {"index": index},
                }
            }
        )
    requests_list.append(
        {
            "createItem": {
                "item": build_text_item(TEXT_QUESTION_TITLE, TEXT_QUESTION_DESCRIPTION),
                "location": {"index": len(CHOICE_QUESTIONS)},
            }
        }
    )

    service.forms().batchUpdate(formId=form_id, body={"requests": requests_list}).execute()
    print(f"{len(requests_list)} questions added.")

    form = service.forms().get(formId=form_id).execute()
    responder_uri = form.get("responderUri", "")
    edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"

    info = {
        "formId": form_id,
        "responderUri": responder_uri,
        "editUrl": edit_url,
    }
    OUTPUT_FILE.write_text(json.dumps(info, indent=2, ensure_ascii=False))

    print()
    print("=" * 70)
    print(f"Form ID       : {form_id}")
    print(f"URL réponse   : {responder_uri}")
    print(f"URL édition   : {edit_url}")
    print("=" * 70)
    print()
    print("PROCHAINES ÉTAPES")
    print()
    print("A. Lier au Sheet + activer les 2 settings non exposés par l'API REST")
    print("   (« Modifier après l'envoi » + désactivation collecte d'e-mails) :")
    print()
    print("   Option 1 — Apps Script (recommandé, scriptable) :")
    print(f"       cd apps_script && clasp run linkAndConfigure  # voir README.md")
    print()
    print("   Option 2 — manuel en 6 clics :")
    print(f"       1. Ouvrir : {edit_url}")
    print("       2. Onglet « Réponses »")
    print("       3. Icône verte Sheets (en haut à droite des réponses)")
    print("       4. « Sélectionner une feuille de calcul existante »")
    print("       5. Choisir le Sheet « RSU_tax_computer » (ou son nom réel)")
    print("       6. Paramètres ⚙ → décocher « Collecter les e-mails », "
          "cocher « Modifier après l'envoi »")


if __name__ == "__main__":
    main()
