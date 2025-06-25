# app/routes/forms/route_preinscription.py
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.schemas.forms.schema_preinscription import PreinscriptionForm
from app.services.forms.service_preinscription import (
    get_programme_info,
    process_preinscription
)
from app.config import TEMPLATE_DIR, settings, get_static_url
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from datetime import datetime, timedelta
from pydantic import ValidationError

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)
templates.env.globals["get_static_url"] = get_static_url

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

@router.post("/api/{programme_id}", response_model=dict)
async def create_preinscription_api(
    programme_id: int,
    form_data: PreinscriptionForm,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint API pour créer une préinscription via JSON
    Accepte les données JSON directement sans passer par le formulaire HTML
    """
    print(f"🚀 [API] Création de préinscription via API pour le programme: {programme_id}")
    try:
        # Vérifier que le programme_id dans les données correspond à l'URL
        if form_data.programme_id != programme_id:
            raise HTTPException(
                status_code=400,
                detail="L'ID du programme dans les données ne correspond pas à l'URL"
            )
        
        # Log des données reçues
        print(f"📋 [API] Données reçues: {form_data.model_dump()}")
        
        # Traiter la préinscription
        result = await process_preinscription(form_data, programme_id, db)
        print(f"✅ [API] Préinscription créée avec succès: {result['id']}")
        
        return {
            "status": "success",
            "message": "Préinscription créée avec succès",
            "data": result
        }
        
    except HTTPException as he:
        print(f"💥 [API] Erreur HTTP: {str(he)}")
        raise
    except ValidationError as ve:
        print(f"💥 [API] Erreur de validation: {str(ve)}")
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "message": "Erreur de validation des données",
                "errors": ve.errors()
            }
        )
    except Exception as e:
        print(f"💥 [API] Erreur serveur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Erreur serveur lors de la création de la préinscription: {str(e)}"
            }
        )