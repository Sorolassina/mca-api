import pandas as pd
import requests
import os

def telecharger_documents_pappers(excel_path, dossier_output, api_key):
    df = pd.read_excel(excel_path, sheet_name="ACT")  

    if not os.path.exists(dossier_output):
        os.makedirs(dossier_output)

    for index, row in df.iterrows():
        token = row.get("Tokens")
        siret = row.get("Siret", f"fichier_{index}")
        type_doc = row.get("Nom_fichier_PDF", "document")

        if pd.isna(token):
            print(f"⚠️ Aucun token pour la ligne {index}")
            continue

        try:
            url = f"https://api.pappers.fr/v2/document/telechargement?token={token}&api_token={api_key}"

            response = requests.get(url)

            if response.status_code == 200:
                nom_fichier = f"{type_doc.replace(' ', '_')}_{siret}.pdf"
                chemin_fichier = os.path.join(dossier_output, nom_fichier)

                with open(chemin_fichier, "wb") as f:
                    f.write(response.content)

                print(f"✅ Fichier téléchargé : {nom_fichier}")
            else:
                print(f"❌ Erreur {response.status_code} pour le token {token}")

        except Exception as e:
            print(f"🚨 Erreur pour le token {token} : {e}")

telecharger_documents_pappers(
    excel_path="C:/Users/SOROLASSINA/Downloads/Candidats Informations ACT.xlsx",
    dossier_output="C:/Users/SOROLASSINA/Downloads/DOCS_ACT",
    api_key="3721812f3ce2b994725e057e906fe35a96ec4ee4209da3f2"
)
