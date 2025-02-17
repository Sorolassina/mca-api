
def get_entreprise_process(data: str):
 
    try:
        return {
            "adresse" :data["siege"].get("adresse", "Adresse non disponible"),
            "nom_entreprise": data.get("nom_entreprise", "N/A"),
            "siret": data["siege"].get("siret", "Adresse non disponible"),
            "siege": data.get("siege", {}),
            "effectif": data.get("effectif", "Non renseigné"),
            "date_creation": data.get("date_creation", "N/A"),
            "code_naf": data.get("code_naf", "N/A"),
            "activite": data.get("activite", "N/A"),
            "etablissements": data.get("etablissements", "N/A"),
            "comptes": data.get("comptes", {}),
            "sites_internet":data.get("sites_internet", "N/A"),
            "dirigeants": [
                {
                    "nom": dirigeant.get("nom", "N/A"),
                    "prenom": dirigeant.get("prenom", "N/A"),
                    "qualite": dirigeant.get("qualite", "N/A")
                }
                for dirigeant in data.get("dirigeants", [])
            ]
        }
    except Exception as e:
        raise ValueError(f"Erreur lors du traitement des données Pappers : {str(e)}")

    
