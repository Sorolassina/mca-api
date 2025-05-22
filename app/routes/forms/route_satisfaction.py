from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.schemas.forms.schema_satisfaction import SatisfactionForm
from app.services.forms.service_satisfaction import process_satisfaction_evenement
from app.models.models import BesoinEvenement, Inscription, Evenement
from app.config import TEMPLATE_DIR, settings
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
logger = logging.getLogger(__name__)

@router.get("/show/{event_id}", response_class=HTMLResponse)
async def show_satisfaction(
    request: Request,
    event_id: Optional[int] = None,
    email: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Affiche le formulaire d'enquête de satisfaction, prérempli si possible."""
    print("\n=== 📋 DÉBUT AFFICHAGE FORMULAIRE SATISFACTION ===")
    print(f"🔍 URL complète: {request.url}")
    print(f"🔍 Query params: {request.query_params}")
    
    # Variables pour le template
    error_message = None
    is_valid = True
    nom = prenom = titre = date_evenement = lieu = ""
    
    # Extraction de l'email depuis les paramètres de l'URL
    email = request.query_params.get("email", "")
    if not email:
        error_message = "L'email est requis pour accéder au formulaire"
        is_valid = False
    
    # Conversion de event_id en entier
    try:
        event_id_int = int(event_id)
    except ValueError:
        error_message = "L'ID de l'événement doit être un nombre"
        is_valid = False
        event_id_int = 0
    
    print(f"🔍 Paramètres extraits:")
    print(f"  - Event ID: {event_id_int}")
    print(f"  - Email: {email}")
    
    if is_valid:
        try:
            async with transaction_manager(db) as db:
                # Vérifier si l'événement existe
                print("\n🔎 Vérification de l'existence de l'événement...")
                result = await db.execute(
                    select(Evenement).where(Evenement.id == event_id_int)
                )
                evenement = result.scalar_one_or_none()
                
                if not evenement:
                    print(f"❌ Événement {event_id_int} non trouvé")
                    error_message = "L'événement n'existe pas dans la base de données"
                    is_valid = False
                else:
                    print(f"✅ Événement trouvé: {evenement.titre}")
                    titre = evenement.titre
                    date_evenement = evenement.date_debut.strftime("%d/%m/%Y")
                    lieu = evenement.lieu
                
                if is_valid:
                    # Vérifier si l'email est inscrit à l'événement
                    print("\n🔎 Vérification de l'inscription...")
                    result = await db.execute(
                        select(Inscription).where(
                            Inscription.event_id == event_id_int,
                            Inscription.email == email
                        )
                    )
                    inscription = result.scalar_one_or_none()
                    
                    if not inscription:
                        print(f"❌ Aucune inscription trouvée pour l'email {email} à l'événement {event_id_int}")
                        error_message = "Vous n'êtes pas inscrit à un programme de formation"
                        is_valid = False
                    else:
                        print(f"✅ Inscription trouvée pour {inscription.nom} {inscription.prenom}")
                        nom = inscription.nom
                        prenom = inscription.prenom
                
        except Exception as e:
            print(f"\n❌ ERREUR INATTENDUE:")
            print(f"  - Type d'erreur: {type(e).__name__}")
            print(f"  - Message: {str(e)}")
            print(f"📋 Traceback complet:\n{traceback.format_exc()}")
            error_message = f"Une erreur est survenue lors de la vérification des données: {str(e)}"
            is_valid = False
    
    print(f"\n📝 Données finales pour le formulaire:")
    print(f"  - Validité: {'✅' if is_valid else '❌'}")
    if error_message:
        print(f"  - Message d'erreur: {error_message}")
    print(f"  - Nom: {nom}")
    print(f"  - Prénom: {prenom}")
    print(f"  - Titre: {titre}")
    print(f"  - Date: {date_evenement}")
    print(f"  - Lieu: {lieu}")
    
    print("\n🎨 Génération du template...")
    response = templates.TemplateResponse(
        "forms/satisfaction.html",
        {
            "request": request,
            "event_id": event_id_int,
            "email": email,
            "nom": nom,
            "prenom": prenom,
            "titre": titre,
            "date_evenement": date_evenement,
            "lieu": lieu,
            "now": datetime.now(),
            "is_valid": is_valid,
            "error_message": error_message,
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
        raise 