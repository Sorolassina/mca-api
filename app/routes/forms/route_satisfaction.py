from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.schemas.forms.schema_satisfaction import SatisfactionForm
from app.services.forms.service_satisfaction import process_satisfaction_evenement
from app.models.models import Evenement
from app.config import TEMPLATE_DIR, settings, get_static_url
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import select
from datetime import datetime
import logging
import traceback
from app.utils.transaction_utils import transaction_manager
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)
# Ajouter la fonction get_static_url aux templates
templates.env.globals["get_static_url"] = get_static_url
logger = logging.getLogger(__name__)

@router.get("/show/{event_id}", response_class=HTMLResponse)
async def show_satisfaction(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Affiche le formulaire d'enquête de satisfaction."""
    print(f"\n=== 📋 DÉBUT AFFICHAGE FORMULAIRE SATISFACTION ===")
    print(f"🔍 Event ID: {event_id}")
    
    try:
        async with transaction_manager(db) as db:
            # Vérifier si l'événement existe
            print("\n🔎 Vérification de l'existence de l'événement...")
            result = await db.execute(
                select(Evenement).where(Evenement.id == event_id)
            )
            evenement = result.scalar_one_or_none()
            
            if not evenement:
                print(f"❌ Événement {event_id} non trouvé")
                raise HTTPException(
                    status_code=404,
                    detail="L'événement n'existe pas"
                )
            
            print(f"✅ Événement trouvé: {evenement.titre}")
            titre = evenement.titre
            date_evenement = evenement.date_debut.strftime("%d/%m/%Y")
            lieu = evenement.lieu or ""
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE:")
        print(f"  - Type d'erreur: {type(e).__name__}")
        print(f"  - Message: {str(e)}")
        print(f"📋 Traceback complet:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors de l'affichage du formulaire: {str(e)}"
        )
    
    print(f"\n📝 Données finales pour le formulaire:")
    print(f"  - Titre: {titre}")
    print(f"  - Date: {date_evenement}")
    print(f"  - Lieu: {lieu}")
    
    print("\n🎨 Génération du template...")
    response = templates.TemplateResponse(
        "forms/satisfaction.html",
        {
            "request": request,
            "event_id": event_id,
            "nom": "",  # Champs vides pour que l'utilisateur les remplisse
            "prenom": "",
            "email": "",
            "titre": titre,
            "date_evenement": date_evenement,
            "lieu": lieu,
            "now": datetime.now(),
            "is_valid": True,  # Toujours valide maintenant
            "error_message": None,
            "config": {"MCA_WEBSITE_URL": settings.MCA_WEBSITE_URL}
        }
    )
    print("✅ Template généré avec succès")
    print("=== FIN AFFICHAGE FORMULAIRE SATISFACTION ===\n")
    return response

@router.post("/submit/{event_id}",include_in_schema=False)
async def submit_satisfaction(
    event_id: int,
    form_data: SatisfactionForm,
    db: AsyncSession = Depends(get_db)
):
    print("\n=== 📤 DÉBUT SOUMISSION FORMULAIRE SATISFACTION ===")
    print(f"📋 Données reçues:")
    print(f"  - Event ID: {event_id}")
    print(f"  - Email: {form_data.email}")
    print(f"  - Nom: {form_data.nom}")
    print(f"  - Prénom: {form_data.prenom}")
    print(f"  - Note globale: {form_data.note_globale}/10")
    print(f"  - Recommandation: {'Oui' if form_data.recommander else 'Non'}")
    
    try:
        print("\n🔄 Traitement de la soumission...")
        result = await process_satisfaction_evenement(form_data, event_id, db)
        print(f"✅ Traitement réussi: {result}")
        print("=== FIN SOUMISSION FORMULAIRE SATISFACTION ===\n")
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE LA SOUMISSION:")
        print(f"  - Type d'erreur: {type(e).__name__}")
        print(f"  - Message: {str(e)}")
        print(f"📋 Traceback complet:\n{traceback.format_exc()}")
        logger.error(f"Erreur lors de la soumission du formulaire de satisfaction: {str(e)}", exc_info=True)
        print("=== FIN SOUMISSION FORMULAIRE SATISFACTION (ERREUR) ===\n")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur lors du traitement de la satisfaction: {str(e)}"
        ) 