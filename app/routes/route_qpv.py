from fastapi import APIRouter,Request
from app.schemas.schema_qpv import Adresse
from app.services.service_qpv import verif_qpv

router = APIRouter()

# On va dans un premier temps récupérer l'adresse géographique et le valider
@router.post("/qpv_check")
async def get_adresse(address:Adresse, request: Request) :
    print("✅ Adresse validée au niveau du route :", address)
    recherche = await verif_qpv(address.model_dump(), request)
    return recherche
