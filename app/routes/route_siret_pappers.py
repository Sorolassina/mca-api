from fastapi import APIRouter, Request
from app.services.service_siret_pappers import get_entreprise_process
from app.schemas.schema_siret import SiretRequest
import time

router = APIRouter()

@router.post("/siret")
async def get_entreprise(siret_request: SiretRequest, request: Request):
     # Exemple de vérification basique de format
    data = siret_request.model_dump()
    start_time = time.time()  # ⏱️ début
    # Vérification basique du format du SIRET
    if 'siret_request' in data:
        sir = data.get("siret_request", "").strip()
        if not (len(sir) == 9 or len(sir) == 14) or not sir.isdigit():
            return {
                "message": "SIRET incorrect",
                "download_url": "",  
                "csv_file": "",
                "entreprise_data": ""
            }
        
    numero_siret = siret_request.numero_siret[:9]

    infosentreprise=await get_entreprise_process(numero_siret, request)

    duration = round(time.time() - start_time, 2)

    print(f"⏱️ execution_time_sec: {duration}")

    return infosentreprise
    