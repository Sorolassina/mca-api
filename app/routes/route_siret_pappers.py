from fastapi import APIRouter, Request
from app.services.service_siret_pappers import get_entreprise_process
from app.schemas.schema_siret import SiretRequest
import time

router = APIRouter()

@router.post("/siret")
async def get_entreprise(siret_request: SiretRequest, request: Request):
    print(f"🚀 [ROUTE] Début du traitement de la requête SIRET")
    print(f"📝 [ROUTE] Données reçues: {siret_request.model_dump()}")
    
    start_time = time.time()
    print("⏱️ [ROUTE] Démarrage du chronomètre")
    
    data = siret_request.model_dump()
    print(f"🔍 [ROUTE] Vérification du format SIRET...")
    
    if 'siret_request' in data:
        sir = data.get("siret_request", "").strip()
        print(f"📊 [ROUTE] Longueur SIRET: {len(sir)}, Contient uniquement des chiffres: {sir.isdigit()}")
        
        if not (len(sir) == 9 or len(sir) == 14) or not sir.isdigit():
            print("❌ [ROUTE] Format SIRET invalide")
            return {
                "message": "SIRET incorrect",
                "download_url": "",  
                "csv_file": "",
                "entreprise_data": ""
            }
    
    numero_siret = siret_request.numero_siret[:9]
    print(f"🔢 [ROUTE] SIRET formaté pour l'API: {numero_siret}")

    print("🔄 [ROUTE] Appel du service get_entreprise_process...")
    try:
        infosentreprise = await get_entreprise_process(numero_siret, request)
        print("✅ [ROUTE] Service exécuté avec succès")
    except Exception as e:
        print(f"❌ [ROUTE] Erreur lors de l'appel au service: {str(e)}")
        raise

    duration = round(time.time() - start_time, 2)
    print(f"⏱️ [ROUTE] Temps d'exécution total: {duration} secondes")

    print("✨ [ROUTE] Envoi de la réponse au client")
    return infosentreprise
    