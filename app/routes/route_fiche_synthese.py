from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from app.schemas.schema_fiche_synthese import FicheSyntheseInput
from app.services.service_fiche_synthese import generate_fiche_synthese

router = APIRouter()

@router.post("/fiche-synthese")
async def create_fiche_synthese(data: FicheSyntheseInput):
    """
    Génère une fiche synthétique en PDF à partir des données fournies.
    """
    try:
        pdf_content = await generate_fiche_synthese(data)
        buffer = BytesIO(pdf_content)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=fiche_synthese_{data.nom}_{data.prenom}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de la fiche synthétique: {str(e)}"
        ) 