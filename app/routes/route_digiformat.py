import requests
from fastapi import APIRouter, HTTPException
from app.config import DIGIFORMA_API_KEY  # Assure-toi d'ajouter la clé API dans ton fichier de config

router = APIRouter()

DIGIFORMA_GRAPHQL_URL = "https://app.digiforma.com/api/v1/graphql"

@router.get("/digiforma")
async def get_digiforma_sessions():
    
    """
    Teste si Digiforma répond avant d'envoyer la requête GraphQL.
    """

    print("🔍 [DEBUG] Test de connexion à Digiforma...")

    try:
        test_response = requests.get(DIGIFORMA_GRAPHQL_URL, timeout=5)  # Test rapide
        print(f"✅ [DEBUG] Réponse Digiforma : {test_response.status_code}")
    except requests.RequestException as e:
        print(f"❌ [DEBUG] Digiforma inaccessible : {e}")
        raise HTTPException(status_code=500, detail="Impossible de contacter Digiforma")



    """
    Récupère les sessions de formation depuis Digiforma via GraphQL.
    """

    # ✅ Définition de la requête GraphQL
    graphql_query = {
        "query": """
        query {
          trainingSessions(filters: {
            pipelineState: FINISHED
            startedAfter: "2023-01-01"
          }) {
            name
            placeName
            code
            place
            pipelineState
            instructors { firstname lastname civility }
            manager { lastname firstname }
            secondManager { lastname firstname }
            program { name trainingType }
            trainees { firstname lastname civility }
            dates { date endTime startTime }
            endDate
            trainingSessionInstructors { instructor { firstname lastname profession civility } }
            trainingType
            type
            specialty
          }
        }
        """
    }

    # ✅ En-têtes avec la clé API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DIGIFORMA_API_KEY}"
    }

    # ✅ Requête POST vers Digiforma
    try:
        response = requests.post(DIGIFORMA_GRAPHQL_URL, json=graphql_query, headers=headers)
        response.raise_for_status()  # Lève une erreur en cas de problème HTTP

        data = response.json()
        if "errors" in data:
            raise HTTPException(status_code=400, detail=f"Erreur GraphQL : {data['errors']}")

        return data["data"]["trainingSessions"]

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à Digiforma : {str(e)}")
