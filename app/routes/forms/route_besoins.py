from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.schemas.forms.schema_besoins import BesoinForm
from app.config import TEMPLATE_DIR, settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from datetime import datetime
from app.services.forms.service_besoins import process_besoin_evenement, get_inscription_and_event_info
from sqlalchemy import select
from app.models.models import Evenement

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/show/{event_id}", response_class=HTMLResponse)
async def show_besoins_form(
    request: Request,
    event_id: int,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Affiche le formulaire d'évaluation des besoins avant événement."""
    print(f"📝 [ROUTE] Affichage du formulaire de besoins pour l'événement {event_id} et l'email {email}")
    
    try:
        # Récupérer les informations de l'inscription et de l'événement
        inscription, evenement = await get_inscription_and_event_info(event_id, email, db)
        
        # Préparer les données pour le template
        template_data = {
            "request": request,
            "event_id": event_id,
            "titre": evenement.titre,
            "description": evenement.description,
            "date_evenement": evenement.date_debut.strftime("%Y-%m-%d"),
            "lieu": evenement.lieu,
            "nom": inscription.nom,
            "prenom": inscription.prenom,
            "email": inscription.email,
            "now": datetime.now(),
            "config": {"MCA_WEBSITE_URL": settings.MCA_WEBSITE_URL}
        }
        
        print(f"✅ [ROUTE] Données préparées pour le template: {template_data}")
        return templates.TemplateResponse("forms/besoins.html", template_data)
        
    except HTTPException as he:
        print(f"💥 [ROUTE] Erreur HTTP: {str(he)}")
        raise
    except Exception as e:
        print(f"💥 [ROUTE] Erreur serveur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors de l'affichage du formulaire: {str(e)}"
        )

@router.post("/submit/{event_id}",include_in_schema=False)
async def submit_besoins_form(
    event_id: int,
    form_data: BesoinForm,
    db: AsyncSession = Depends(get_db)
):
    """Traite la soumission du formulaire d'évaluation des besoins."""
    print(f"📝 [ROUTE] Soumission du formulaire de besoins pour l'événement {event_id}")
    
    try:
        # Récupérer les informations de l'événement
        result_event = await db.execute(
            select(Evenement).where(Evenement.id == event_id)
        )
        evenement = result_event.scalar_one_or_none()
        
        if not evenement:
            print(f"❌ [ROUTE] Événement {event_id} non trouvé")
            raise HTTPException(
                status_code=404,
                detail="L'événement n'existe pas"
            )
        
        # Traiter la soumission
        result = await process_besoin_evenement(
            form_data=form_data,
            event_id=event_id,
            titre=evenement.titre,
            description=evenement.description or "",
            date_evenement=evenement.date_debut.strftime("%Y-%m-%d"),
            lieu=evenement.lieu or "",
            db=db
        )
        
        print(f"✅ [ROUTE] Besoins enregistrés avec succès pour l'événement {event_id}")
        return JSONResponse(status_code=200, content=result)
        
    except HTTPException as he:
        print(f"💥 [ROUTE] Erreur HTTP: {str(he)}")
        raise
    except Exception as e:
        print(f"💥 [ROUTE] Erreur serveur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors du traitement des besoins: {str(e)}"
        ) 