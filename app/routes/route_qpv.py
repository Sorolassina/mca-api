from fastapi import APIRouter,Request
from app.schemas.schema_qpv import Adresse
from app.services.service_qpv import verif_qpv
import time

router = APIRouter()

# On va dans un premier temps récupérer l'adresse géographique et le valider
@router.post("/qpv_check")
async def get_adresse(address:Adresse, request: Request) :

    start_time = time.time()  # ⏱️ début
    data = address.model_dump()

    print("✅ Adresse validée au niveau du route :", address)

    # Vérifie si tous les champs sont vides
    if all(value is None or value == '' for value in data.values()):
        return {
            "address": "Adresse mal formatté",
            "nom_qp": "Aucun QPV",
            "distance_m": "N/A",
            "carte": "",
            "image_url":"",
            "image_encoded": ""
        }
    
    # Exemple de vérification basique de format
    if 'adresse' in data:
        adr = data.get("adresse", "").strip()
        if len(adr) < 5 or adr.isdigit():
            return {
            "address": "Adresse mal formatté",
            "nom_qp": "Aucun QPV",
            "distance_m": "N/A",
            "carte": "",
            "image_url":"",
            "image_encoded": ""
        }

    # Si tout est OK, on continue la vérification QPV
    recherche = await verif_qpv(data, request)

    duration = round(time.time() - start_time, 2)

    print("✅ fin d'exécution :", address)

    print(f"⏱️ execution_time_sec: {duration}")

    return recherche
