from fastapi import Request
import csv
from app.config import get_base_url
from app.utils.file_encoded import encode_file_to_base64
from app.config import FICHIERS_DIR
import os
import requests
from fastapi import HTTPException
from app.config import PAPPERS_API_KEY
      
async def get_entreprise_process(numero_siret: str, request: Request):
 
    url = f"https://api.pappers.fr/v2/entreprise?siren={numero_siret}&api_token={PAPPERS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # ✅ Vérifie si la requête a réussi (code 200)
        data = response.json()
               
        if not data.get("siren") :
            raise HTTPException(status_code=404, detail="🚨 Entreprise non trouvée")

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=f"❌ Erreur API Pappers : {str(e)}")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"🚨 Erreur de connexion à Pappers : {str(e)}")

    base_url = get_base_url(request)  # Récupérer l'URL dynamique
    csv_url = os.path.join(FICHIERS_DIR, "entreprise_data.csv")
    """ Générer et retourner les données JSON + CSV """
    try:
        
        # 📌 Vérifier si "comptes" existe et est une liste
        comptes = data.get("comptes", [])
        comptes_disponibles = [
        compte for compte in comptes if compte.get("nom_fichier_pdf") is not None
        ]

        # 📌 Générer le fichier CSV
        with open(csv_url, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow([
                "Nom Entreprise", "Siret", "Adresse", "Effectif",
                "Date Création", "Code NAF", "Activité",
                "Année clôture", "Date dépôt", "Type comptes",
                "Nom fichier PDF", "Tokens"
            ])

            for compte in comptes_disponibles:
                writer.writerow([
                    data.get("nom_entreprise", "N/A"),
                    data["siege"].get("siret", "Adresse non disponible"),
                    data["siege"].get("adresse", "Adresse non disponible"),
                    data.get("effectif", "Non renseigné"),
                    data.get("date_creation", "N/A"),
                    data.get("code_naf", "N/A"),
                    data.get("activite", "N/A"),
                    compte.get("annee_cloture", "N/A"),
                    compte.get("date_depot_formate", "N/A"),
                    compte.get("type_comptes", "N/A"),
                    compte.get("nom_fichier_pdf", "N/A"),
                    compte.get("token", "N/A")
                ])

        # Vérifie si l’image existe avant d’essayer de l’encoder
        if os.path.exists(csv_url):
            csv_base64 = encode_file_to_base64(csv_url)
        else:
            csv_base64 = None  # Si le fichier n’existe pas

        pdf_path = f"{base_url}/fichiers/entreprise_data.csv"  # 📌 Utiliser le bon chemin
       
        # 📌 Retourner JSON + lien téléchargement
        return {
        "message": "Données extraites avec succès",
        "download_url": pdf_path,  
        "csv_file": csv_base64,  # 📄 Contenu CSV encodé
        "entreprise_data": comptes_disponibles  # 📊 Données JSON
        }

    except Exception as e:
        raise ValueError(f"Erreur lors du traitement des données Pappers : {str(e)}")


