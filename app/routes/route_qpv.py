from fastapi import APIRouter, File, HTTPException,Request
from fastapi.responses import FileResponse

from app.schemas.schema_qpv import Adresse
from app.services.service_qpv import verif_qpv

router = APIRouter()

# On va dans un premier temps récupérer l'adresse géographique et le valider
@router.post("/qpv_check")
def get_adresse(address:Adresse, request: Request) :
    recherche = verif_qpv(address.dict(), request)

    return recherche
