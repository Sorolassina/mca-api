from fastapi import HTTPException
from app.schemas.forms.schema_inscription import InscriptionForm
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import Preinscription, Inscription, SituationProfessionnelle, NiveauEtude
from app.utils.transaction_utils import transaction_manager
from app.utils.sequence_utils import diagnose_sequence, reset_sequence

async def process_inscription(
    form_data: InscriptionForm,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Traite l'inscription en deux étapes :
    1. Vérifie que la personne a bien fait une préinscription (existe dans preinscriptions)
    2. Vérifie qu'elle n'a pas déjà une inscription (n'existe pas dans inscriptions)
    """
    print(f"📝 [SERVICE] Traitement de l'inscription pour le programme: {form_data.programme_id}")
    print(f"📋 [SERVICE] Données du formulaire: {form_data.model_dump()}")
    
    try:
        # Convertir programme_id en entier
        try:
            programme_id_int = int(form_data.programme_id)
        except ValueError:
            print(f"💥 [SERVICE] ID de programme invalide: {form_data.programme_id}")
            raise HTTPException(
                status_code=400,
                detail="L'ID du programme doit être un nombre entier"
            )

        # Diagnostic de la séquence avant la création
        diagnosis = await diagnose_sequence(db, "inscriptions")
        if not diagnosis["is_healthy"]:
            print("⚠️ [SERVICE] Séquence non saine détectée, tentative de réinitialisation...")
            await reset_sequence(db, "inscriptions")

        async with transaction_manager(db) as session:
            # Étape 1: Vérifier l'existence de la préinscription
            print("🔍 [SERVICE] Vérification de la préinscription...")
            stmt_preinscription = select(Preinscription).where(
                and_(
                    Preinscription.programme_id == programme_id_int,  # Utiliser l'ID converti en entier
                    Preinscription.email == form_data.email,
                    Preinscription.nom == form_data.nom,
                    Preinscription.prenom == form_data.prenom
                )
            )
            result_preinscription = await session.execute(stmt_preinscription)
            preinscription = result_preinscription.scalar_one_or_none()
            
            if not preinscription:
                print(f"⚠️ [SERVICE] Aucune préinscription trouvée pour email={form_data.email}, nom={form_data.nom}, prenom={form_data.prenom}")
                raise HTTPException(
                    status_code=400,
                    detail="Vous devez d'abord être préinscrit pour pouvoir vous inscrire à ce programme."
                )

            # Étape 2: Vérifier qu'il n'existe pas déjà une inscription
            print("🔍 [SERVICE] Vérification des inscriptions existantes...")
            stmt_inscription = select(Inscription).where(
                and_(
                    Inscription.programme_id == programme_id_int,  # Utiliser l'ID converti en entier
                    Inscription.email == form_data.email,
                    Inscription.nom == form_data.nom,
                    Inscription.prenom == form_data.prenom
                )
            )
            result_inscription = await session.execute(stmt_inscription)
            existing_inscription = result_inscription.scalar_one_or_none()
            
            if existing_inscription:
                print(f"⚠️ [SERVICE] Inscription déjà existante pour email={form_data.email}, nom={form_data.nom}, prenom={form_data.prenom}")
                raise HTTPException(
                    status_code=400,
                    detail="Une inscription existe déjà pour cette personne dans ce programme."
                )

            # Si on arrive ici, on peut créer l'inscription
            print("📝 [SERVICE] Création de l'inscription...")

            # Créer l'instance Inscription
            inscription_db = Inscription(
                programme_id=programme_id_int,  # Utiliser l'ID converti en entier
                preinscription_id=preinscription.id,  # Utiliser l'ID de la préinscription trouvée
                nom=form_data.nom,
                prenom=form_data.prenom,
                email=form_data.email,
                telephone=form_data.telephone,
                date_naissance=form_data.date_naissance,
                adresse=form_data.adresse,
                code_postal=form_data.code_postal,
                ville=form_data.ville,
                situation_professionnelle=SituationProfessionnelle(form_data.situation_professionnelle),
                niveau_etude=NiveauEtude(form_data.niveau_etude),
                projet_entrepreneurial=form_data.projet_entrepreneurial,
                rgpd_consent=form_data.rgpd_consent,
                rgpd_consent_date=form_data.rgpd_consent_date or datetime.now().date(),
                date_inscription=datetime.now().date(),
                source=form_data.source or "formulaire_web"
            )

            # Sauvegarder dans la base de données
            session.add(inscription_db)
            await session.flush()
            print(f"💾 [SERVICE] Inscription sauvegardée dans la base de données avec l'ID: {inscription_db.id}")

            result = {
                "id": inscription_db.id,  # Utiliser l'ID généré par la base de données
                "status": "success",
                "message": "Inscription enregistrée avec succès",
                "programme_id": programme_id_int  # Utiliser l'ID converti en entier
            }
            print(f"✅ [SERVICE] Inscription traitée avec succès: {inscription_db.id}")
            print(f"📊 [SERVICE] Résultat final: {result}")
            return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 [SERVICE] Erreur lors du traitement de l'inscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de l'inscription: {str(e)}"
        )
