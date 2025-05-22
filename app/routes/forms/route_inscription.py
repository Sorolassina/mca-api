from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.schemas.forms.schema_inscription import InscriptionForm
from app.services.forms.service_inscription import process_inscription
from app.config import TEMPLATE_DIR
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
import logging
from datetime import datetime
from app.models.models import SituationProfessionnelle, NiveauEtude, Preinscription
from sqlalchemy import select
from app.services.forms.service_preinscription import get_programme_info
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/show/{programme_id}/{email}", response_class=HTMLResponse)
async def show_inscription(
    request: Request,
    programme_id: int,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Affiche le formulaire d'inscription, prérempli si une préinscription existe pour ce programme et cet email."""
    try:
        # Convertir programme_id en entier
        programme_id_int = int(programme_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="L'ID du programme doit être un nombre entier"
        )

    programme_info = await get_programme_info(programme_id_int, db)
    result = await db.execute(
        select(Preinscription).where(
            Preinscription.programme_id == programme_id_int,  # Utiliser l'entier
            Preinscription.email == email
        )
    )
    preinscription = result.scalar_one_or_none()
    situation_choices = [(e.value, e.name.replace('_', ' ').capitalize()) for e in SituationProfessionnelle]
    niveau_choices = [(e.value, e.name.replace('_', ' ').capitalize()) for e in NiveauEtude]
    return templates.TemplateResponse(
        "forms/inscription.html",
        {
            "request": request,
            "programme_id": programme_id_int,  # Passer l'entier au template
            "programme_info": programme_info,
            "preinscription": preinscription,
            "now": datetime.now(),
            "situation_choices": situation_choices,
            "niveau_choices": niveau_choices,
        }
    )

@router.post("/submit/{programme_id}",include_in_schema=False)
async def submit_inscription(
    programme_id: int,
    form_data: InscriptionForm,
    db: AsyncSession = Depends(get_db)
):
    """Traite la soumission du formulaire d'inscription"""
    print(f"📝 [ROUTE] Soumission du formulaire d'inscription pour le programme: {programme_id}")
    try:
        # S'assurer que le programme_id du formulaire correspond à celui de l'URL
        if form_data.programme_id != programme_id:
            print(f"⚠️ [ROUTE] Incohérence entre programme_id URL ({programme_id}) et formulaire ({form_data.programme_id})")
            raise HTTPException(
                status_code=400,
                detail="L'ID du programme dans le formulaire ne correspond pas à l'URL"
            )

        result = await process_inscription(form_data, db)
        print(f"✅ [ROUTE] Inscription traitée avec succès: {result['id']}")
        return JSONResponse(status_code=200, content=result)
    except HTTPException as he:
        print(f"💥 [ROUTE] Erreur HTTP lors du traitement de l'inscription: {str(he)}")
        raise
    except Exception as e:
        print(f"💥 [ROUTE] Erreur serveur lors du traitement de l'inscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors du traitement de l'inscription: {str(e)}"
        )
