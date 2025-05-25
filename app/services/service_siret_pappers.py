from fastapi import Request
import csv
from app.config import get_base_url
from app.utils.file_encoded import encode_file_to_base64
from app.config import FICHIERS_DIR
import os
import requests
from fastapi import HTTPException
from app.config import settings
      
async def get_entreprise_process(numero_siret: str, request: Request):
    print(f"🚀 [SERVICE] Début get_entreprise_process pour SIRET: {numero_siret}")
    print(f"🔑 [SERVICE] Utilisation de l'API key: {settings.PAPPERS_API_KEY[:5]}...")
 
    url = f"https://api.pappers.fr/v2/entreprise?siren={numero_siret}&api_token={settings.PAPPERS_API_KEY}"
    print(f"🌐 [SERVICE] Appel API Pappers: {url}")

    try:
        print("📡 [SERVICE] Envoi de la requête à l'API Pappers...")
        response = requests.get(url)
        print(f"📥 [SERVICE] Réponse reçue - Status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"✅ [SERVICE] Données JSON reçues: {bool(data)}")
               
        if not data.get("siren"):
            print("❌ [SERVICE] Entreprise non trouvée dans la réponse")
            raise HTTPException(status_code=404, detail="🚨 Entreprise non trouvée")

    except requests.exceptions.HTTPError as e:
        print(f"❌ [SERVICE] Erreur HTTP: {str(e)}")
        raise HTTPException(status_code=response.status_code, detail=f"❌ Erreur API Pappers : {str(e)}")

    except requests.exceptions.RequestException as e:
        print(f"❌ [SERVICE] Erreur de connexion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"🚨 Erreur de connexion à Pappers : {str(e)}")

    base_url = get_base_url(request)
    print(f"🌐 [SERVICE] URL de base: {base_url}")
    csv_url = os.path.join(FICHIERS_DIR, "entreprise_data.csv")
    print(f"📁 [SERVICE] Chemin du fichier CSV: {csv_url}")

    try:
        print("📊 [SERVICE] Traitement des données comptables...")
        comptes = data.get("comptes", [])
        print(f"📈 [SERVICE] Nombre total de comptes trouvés: {len(comptes)}")
        
        comptes_disponibles = [
            compte for compte in comptes if compte.get("nom_fichier_pdf") is not None
        ]
        print(f"📊 [SERVICE] Nombre de comptes avec PDF disponibles: {len(comptes_disponibles)}")

        print("📝 [SERVICE] Génération du fichier CSV...")
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
        print("✅ [SERVICE] Fichier CSV généré avec succès")

        print("🔍 [SERVICE] Vérification de l'existence du fichier CSV...")
        if os.path.exists(csv_url):
            print("📄 [SERVICE] Encodage du fichier CSV en base64...")
            csv_base64 = encode_file_to_base64(csv_url)
            print("✅ [SERVICE] Encodage CSV terminé")
        else:
            print("⚠️ [SERVICE] Fichier CSV non trouvé")
            csv_base64 = None

        pdf_path = f"{base_url}/fichiers/entreprise_data.csv"
        print(f"🔗 [SERVICE] URL de téléchargement générée: {pdf_path}")
       
        print("✨ [SERVICE] Préparation de la réponse finale...")
        
        # Préparation des données essentielles de l'entreprise
        entreprise_info = {
            "siren": data.get("siren"),
            "nom_entreprise": data.get("nom_entreprise"),
            "denomination": data.get("denomination"),
            "forme_juridique": data.get("forme_juridique"),
            "date_creation": data.get("date_creation"),
            "date_creation_formate": data.get("date_creation_formate"),
            "capital": data.get("capital"),
            "capital_formate": data.get("capital_formate"),
            "code_naf": data.get("code_naf"),
            "libelle_code_naf": data.get("libelle_code_naf"),
            "activite": data.get("objet_social"),
            "effectif": data.get("effectif"),
            "siege": {
                "adresse": data.get("siege", {}).get("adresse_ligne_1"),
                "code_postal": data.get("siege", {}).get("code_postal"),
                "ville": data.get("siege", {}).get("ville"),
                "siret": data.get("siege", {}).get("siret")
            },
            "representants": data.get("representants", []),
            "derniers_statuts": data.get("derniers_statuts"),
            "publications_bodacc": data.get("publications_bodacc", []),
            "comptes": comptes_disponibles  # On garde les comptes s'il y en a
        }
        
        print("📊 [SERVICE] Données de l'entreprise extraites avec succès")
        
        response_data = {
            "message": "Données extraites avec succès",
            "entreprise_data": entreprise_info  # On utilise les données complètes
        }
        print("✅ [SERVICE] Traitement terminé avec succès")
        return response_data

    except Exception as e:
        print(f"❌ [SERVICE] Erreur lors du traitement: {str(e)}")
        raise ValueError(f"Erreur lors du traitement des données Pappers : {str(e)}")


