from fastapi import HTTPException
from app.schemas.forms.schema_besoins import BesoinForm
from app.models.models import BesoinEvenement, Inscription, Evenement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
from typing import Dict, Any, Optional, Tuple

async def get_inscription_and_event_info(
    event_id: int,
    email: str,
    db: AsyncSession
) -> Tuple[Optional[Inscription], Optional[Evenement]]:
    """
    Récupère les informations de l'inscription et de l'événement pour un email donné.
    Retourne un tuple (inscription, evenement) ou lève une exception si non trouvé.
    """
    print(f"🔍 [SERVICE] Recherche de l'inscription pour l'événement {event_id} et l'email {email}")
    
    # Vérifier si l'événement existe
    result_event = await db.execute(
        select(Evenement).where(Evenement.id == event_id)
    )
    evenement = result_event.scalar_one_or_none()
    
    if not evenement:
        print(f"❌ [SERVICE] Événement {event_id} non trouvé")
        raise HTTPException(
            status_code=404,
            detail="L'événement n'existe pas"
        )
    
    # Vérifier si l'inscription existe
    result_inscription = await db.execute(
        select(Inscription).where(
            Inscription.email == email
        )
    )
    inscription = result_inscription.scalar_one_or_none()
    
    if not inscription:
        print(f"❌ [SERVICE] Aucune inscription trouvée pour l'email {email} à un programme")
        raise HTTPException(
            status_code=404,
            detail="Vous n'êtes pas inscrit à cet événement"
        )
    
    print(f"✅ [SERVICE] Inscription trouvée pour {inscription.nom} {inscription.prenom}")
    return inscription, evenement

async def process_besoin_evenement(
    form_data: BesoinForm,
    event_id: str,
    titre: str,
    description: str = "",
    date_evenement: str = "",
    nb_jours: int = 1,
    lieu: str = "",
    db: AsyncSession = None
) -> Dict[str, Any]:
    """
    Traite la soumission d'un besoin avant événement :
    - Convertit la date
    - Crée et enregistre l'objet en base
    - Retourne un dict de résultat
    """
    try:
        # Conversion de la date_evenement (str) en objet date
        date_evenement_obj = None
        if date_evenement:
            try:
                date_evenement_obj = datetime.strptime(date_evenement, "%Y-%m-%d").date()
            except Exception:
                date_evenement_obj = None
        besoin_id = f"besoin_{event_id}_{uuid.uuid4().hex[:8]}"
        besoin_db = BesoinEvenement(
            id=besoin_id,
            event_id=event_id,
            titre=titre,
            description=description,
            date_evenement=date_evenement_obj,
            nb_jours=nb_jours,
            lieu=lieu,
            nom=form_data.nom,
            prenom=form_data.prenom,
            email=form_data.email,
            besoins_principaux=form_data.besoins_principaux,
            attentes=form_data.attentes,
            niveau_connaissance=form_data.niveau_connaissance,
            objectifs=form_data.objectifs,
            contraintes=form_data.contraintes,
            is_participant=form_data.is_participant,
            rgpd_consent=form_data.rgpd_consent,
            rgpd_consent_date=form_data.rgpd_consent_date or datetime.now().date(),
            date_soumission=datetime.now().date(),
        )
        db.add(besoin_db)
        await db.commit()
        await db.refresh(besoin_db)
        return {"status": "success", "message": "Besoins enregistrés avec succès."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement des besoins: {str(e)}") 