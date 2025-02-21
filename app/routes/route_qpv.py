from fastapi import APIRouter, File, HTTPException
from fastapi.responses import FileResponse

from app.models.model_qpv import Adresse
from app.services.service_qpv import verif_qpv

router = APIRouter()

# On va dans un premier temps récupérer l'adresse géographique et le valider
@router.post("/qpv_check")
def get_adresse(address:Adresse) :
    print (address)
    recherche = verif_qpv(address.dict())

    return recherche
