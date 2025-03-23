from fastapi import APIRouter, Request
from app.services.service_siret_pappers import get_entreprise_process
from app.schemas.schema_siret import SiretRequest

router = APIRouter()

@router.post("/siret")
async def get_entreprise(siret_request: SiretRequest, request: Request):
    numero_siret = siret_request.numero_siret[:9]
    return await get_entreprise_process(numero_siret, request)
    