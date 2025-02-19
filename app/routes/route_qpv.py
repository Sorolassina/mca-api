from fastapi import APIRouter, File, HTTPException
from fastapi.responses import FileResponse

from app.models.model_qpv import Adresse
from app.services.service_qpv import verif_qpv

router = APIRouter()

# On va dans un premier temps récupérer l'adresse géographique et le valider
@router.post("/qpv-check/")
def get_adresse(address:Adresse) :
    recherche = verif_qpv(address.dict())

    # Récupérer l'URL du fichier HTML
    map_url = recherche.get("carte_url")

    return recherche
