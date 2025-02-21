from fastapi import APIRouter, HTTPException
import requests
from app.config import PAPPERS_API_KEY
from app.services.service_siret_pappers import get_entreprise_process
from app.models.model_siret import SiretRequest

router = APIRouter()

@router.post("/siret")
def get_entreprise(request: SiretRequest):

    numero_siret=request.numero_siret

    url = f"https://api.pappers.fr/v2/entreprise?siret={numero_siret}&api_token={PAPPERS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # ✅ Vérifie si la requête a réussi (code 200)
        data = response.json()
        
        if not data.get("siren") :
            raise HTTPException(status_code=404, detail="🚨 Entreprise non trouvée")

        return get_entreprise_process(data)  # ✅ Utilisation correcte du service

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=f"❌ Erreur API Pappers : {str(e)}")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"🚨 Erreur de connexion à Pappers : {str(e)}")
