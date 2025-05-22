from fastapi import HTTPException
from app.schemas.forms.schema_satisfaction import SatisfactionForm
from app.models.models import SatisfactionEvenement
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import traceback
from typing import Dict, Any
from app.utils.transaction_utils import transaction_manager
from app.utils.sequence_utils import diagnose_sequence, reset_sequence

async def process_satisfaction_evenement(
    form_data: SatisfactionForm,
    event_id: int,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """
    Traite la soumission d'une enquête de satisfaction post-événement.
    """
    print("\n=== 📝 DÉBUT TRAITEMENT ENQUÊTE DE SATISFACTION ===")
    try:
        print(f"📋 Données reçues pour l'événement {event_id}:")
        print(f"  - Email: {form_data.email}")
        print(f"  - Nom: {form_data.nom}")
        print(f"  - Prénom: {form_data.prenom}")
        print(f"  - Note globale: {form_data.note_globale}/10")
        print(f"  - Recommandation: {'Oui' if form_data.recommander else 'Non'}")
        
        async with transaction_manager(db) as db:
            # Diagnostic de la séquence avant traitement
            print("\n🔍 Diagnostic de la séquence avant traitement...")
            await diagnose_sequence(db, "satisfaction_evenement_id_seq")
            
            # Création de l'objet satisfaction
            print("\n📦 Création de l'objet SatisfactionEvenement...")
            satisfaction_db = SatisfactionEvenement(
                event_id=event_id,
                email=form_data.email,
                nom=form_data.nom,
                prenom=form_data.prenom,
                note_globale=form_data.note_globale,
                points_positifs=form_data.points_positifs,
                points_amelioration=form_data.points_amelioration,
                recommander=form_data.recommander,
                commentaires=form_data.commentaires,
                opinion_evaluateur=form_data.opinion_evaluateur,
                rgpd_consent=form_data.rgpd_consent,
                rgpd_consent_date=form_data.rgpd_consent_date or datetime.now().date(),
                date_soumission=datetime.now().date(),
            )
            
            # Enregistrement en base
            print("\n💾 Enregistrement en base de données...")
            db.add(satisfaction_db)
            await db.commit()
            print("✅ Commit réussi")
            
            # Rafraîchissement de l'objet
            print("\n🔄 Rafraîchissement de l'objet...")
            await db.refresh(satisfaction_db)
            print(f"✅ Objet rafraîchi: ID={satisfaction_db.id}")
            
            # Vérification de la séquence après traitement
            print("\n🔍 Diagnostic de la séquence après traitement...")
            await diagnose_sequence(db, "satisfaction_evenement_id_seq")
            
            # Si la séquence est désynchronisée, on la réinitialise
            if await diagnose_sequence(db, "satisfaction_evenement_id_seq")["is_desynchronized"]:
                print("\n⚠️ Séquence désynchronisée détectée, réinitialisation...")
                await reset_sequence(db, "satisfaction_evenement_id_seq")
                print("✅ Séquence réinitialisée")
            
            print("\n🎉 ENQUÊTE DE SATISFACTION ENREGISTRÉE AVEC SUCCÈS")
            print("=== FIN TRAITEMENT ENQUÊTE DE SATISFACTION ===\n")
            return {"status": "success", "message": "Merci pour votre retour !"}
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU TRAITEMENT:")
        print(f"  - Type d'erreur: {type(e).__name__}")
        print(f"  - Message: {str(e)}")
        print(f"📋 Traceback complet:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enregistrement de la satisfaction: {str(e)}"
        ) 