# app/routes/forms/route_preinscription.py
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.schemas.forms.schema_preinscription import PreinscriptionForm
from app.services.forms.service_preinscription import (
    get_programme_info,
    process_preinscription
)
from app.config import TEMPLATE_DIR, settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from datetime import datetime, timedelta
from pydantic import ValidationError

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/show/{programme_id}", response_class=HTMLResponse)
async def show_preinscription(
    request: Request,
    programme_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Affiche le formulaire de préinscription"""
    print(f"🎯 [ROUTE] Affichage du formulaire de préinscription pour le programme: {programme_id}")
    try:
        # Récupérer les informations du programme
        programme_info = await get_programme_info(programme_id, db)
        print(f"✨ [ROUTE] Informations du programme récupérées: {programme_info['nom']}")
        
        return templates.TemplateResponse(
            "forms/preinscription.html",
            {
                "request": request,
                "programme_info": programme_info,
                "programme_id": programme_id,
                "now": datetime.now(),
                "timedelta": timedelta,
                "config": {"MCA_WEBSITE_URL": settings.MCA_WEBSITE_URL}
            }
        )
    except HTTPException as he:
        # Propager les erreurs HTTP telles quelles
        print(f"💥 [ROUTE] Erreur HTTP lors de l'affichage du formulaire: {str(he)}")
        raise
    except Exception as e:
        # Les autres erreurs sont des erreurs serveur
        print(f"💥 [ROUTE] Erreur serveur lors de l'affichage du formulaire: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors de l'affichage du formulaire: {str(e)}"
        )

@router.post("/submit/{programme_id}",include_in_schema=False)
async def submit_preinscription(
    programme_id: int,
    form_data: PreinscriptionForm,
    db: AsyncSession = Depends(get_db)
):
    """Traite la soumission du formulaire de préinscription"""
    print(f"📝 [ROUTE] Soumission du formulaire de préinscription pour le programme: {programme_id}")
    try:
        # Log des données reçues
        print(f"📋 [ROUTE] Données reçues: {form_data.model_dump()}")
        
        result = await process_preinscription(form_data, programme_id, db)
        print(f"✅ [ROUTE] Préinscription traitée avec succès: {result['id']}")
        return result
    except HTTPException as he:
        # Propager les erreurs HTTP telles quelles
        print(f"💥 [ROUTE] Erreur HTTP lors du traitement de la préinscription: {str(he)}")
        raise
    except Exception as e:
        # Les autres erreurs sont des erreurs serveur
        print(f"💥 [ROUTE] Erreur serveur lors du traitement de la préinscription: {str(e)}")
        if isinstance(e, ValidationError):
            # Log détaillé des erreurs de validation
            for error in e.errors():
                print(f"⚠️ [ROUTE] Erreur de validation - Champ: {error['loc']}, Message: {error['msg']}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors du traitement de la préinscription: {str(e)}"
        )