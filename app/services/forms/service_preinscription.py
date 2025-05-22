# app/services/forms/service_preinscription.py
from fastapi import HTTPException
from app.schemas.forms.schema_preinscription import PreinscriptionForm
from datetime import datetime, date
import json
import os
from app.config import FICHIERS_DIR
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import Programme, Preinscription, SituationProfessionnelle, NiveauEtude
from app.utils.transaction_utils import transaction_manager


def serialize_dates(obj: Any) -> Any:
    """Convertit les objets date en chaînes de caractères pour la sérialisation JSON"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj

async def get_programme_info(programme_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Récupère les informations d'un programme à partir de son ID.
    """
    print(f"🔍 [SERVICE] Récupération des informations du programme: {programme_id}")
    try:
        # Convertir programme_id en entier
        try:
            programme_id_int = int(programme_id)
        except ValueError:
            print(f"💥 [SERVICE] ID de programme invalide: {programme_id}")
            raise HTTPException(
                status_code=400,
                detail="L'ID du programme doit être un nombre entier"
            )

        async with transaction_manager(db) as session:
            # Requête pour récupérer le programme
            stmt = select(Programme).where(Programme.id == programme_id_int)
            result = await session.execute(stmt)
            programme = result.scalar_one_or_none()
            
            if not programme:
                print(f"⚠️ [SERVICE] Programme non trouvé avec l'ID: {programme_id_int}")
                raise HTTPException(
                    status_code=404,
                    detail="Programme non trouvé"
                )
            
            # Retourner les informations du programme avec gestion sécurisée des dates
            try:
                programme_info = {
                    "id": programme.id,
                    "nom": programme.nom,
                    "description": programme.description,
                    "date_debut": programme.date_debut.isoformat() if programme.date_debut else None,
                    "date_fin": programme.date_fin.isoformat() if programme.date_fin else None,
                    "lieu": programme.lieu,
                    "places_disponibles": programme.places_disponibles,
                    "places_totales": programme.places_totales,
                    "statut": programme.statut.value if programme.statut else None,
                    "prix": programme.prix
                }
                print(f"📊 [SERVICE] Informations du programme formatées: {programme_info}")
                return programme_info
            except Exception as format_error:
                print(f"💥 [SERVICE] Erreur lors du formatage des données du programme: {str(format_error)}")
                raise
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 [SERVICE] Erreur lors de la récupération du programme: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des informations du programme: {str(e)}"
        )

async def check_duplicate_preinscription(
    email: str,
    programme_id: int,
    db: AsyncSession
) -> bool:
    """
    Vérifie si une préinscription existe déjà pour cet email et ce programme.
    Retourne True si un doublon est trouvé, False sinon.
    """
    print(f"🔍 [SERVICE] Vérification des doublons pour email: {email}, programme: {programme_id}")
    print(f"🔌 [SERVICE] Session DB active: {db.is_active}")
    
    try:
        # Normalisation de l'email
        normalized_email = email.lower().strip()
        print(f"📧 [SERVICE] Email normalisé: {normalized_email}")
        
        async with transaction_manager(db) as session:
            # Recherche d'une préinscription existante
            stmt = select(Preinscription).where(
                and_(
                    Preinscription.email == email.lower().strip(),  # Normalisation de l'email
                    Preinscription.programme_id == programme_id
                )
            )
            print(f"🔎 [SERVICE] Requête SQL: {stmt}")
            
            # Exécuter la requête
            print("⚡ [SERVICE] Exécution de la requête de vérification des doublons...")
            result = await session.execute(stmt)
            print("✅ [SERVICE] Requête exécutée avec succès")
            
            # Récupérer le résultat
            existing_preinscription = result.scalar_one_or_none()
            print(f"📝 [SERVICE] Résultat de la recherche: {existing_preinscription}")
            
            if existing_preinscription:
                print(f"⚠️ [SERVICE] Doublon détecté - Email: {normalized_email}, Programme: {programme_id}")
                return True
                
            print(f"✅ [SERVICE] Aucun doublon trouvé pour email: {normalized_email}, programme: {programme_id}")
            return False
            
    except Exception as e:
        print(f"💥 [SERVICE] Erreur inattendue lors de la vérification des doublons: {str(e)}")
        print(f"🔍 [SERVICE] Type d'erreur: {type(e)}")
        print(f"📋 [SERVICE] Arguments de l'erreur: {e.args}")
        raise HTTPException(
            status_code=500,
            detail=f"Une erreur inattendue s'est produite lors de la vérification des doublons: {str(e)}"
        )

async def process_preinscription(
    form_data: PreinscriptionForm,
    programme_id: int,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """
    Traite la préinscription et stocke les données dans la base de données et un fichier JSON.
    """
    print(f"📝 [SERVICE] Traitement de la préinscription pour le programme: {programme_id}")
    print(f"📋 [SERVICE] Données du formulaire: {form_data.model_dump()}")
    print(f"🔌 [SERVICE] Session DB: {db}")
    
    try:
        # Convertir programme_id en entier
        try:
            programme_id_int = int(programme_id)
        except ValueError:
            print(f"💥 [SERVICE] ID de programme invalide: {programme_id}")
            raise HTTPException(
                status_code=400,
                detail="L'ID du programme doit être un nombre entier"
            )

        async with transaction_manager(db) as session:
            # Vérifier si le programme existe et a des places disponibles
            print("🔍 [SERVICE] Vérification des informations du programme...")
            stmt = select(Programme).where(Programme.id == programme_id_int)
            result = await session.execute(stmt)
            programme = result.scalar_one_or_none()
            
            if not programme:
                print(f"⚠️ [SERVICE] Programme non trouvé avec l'ID: {programme_id_int}")
                raise HTTPException(status_code=404, detail="Programme non trouvé")
                
            if programme.places_disponibles <= 0:
                print(f"⚠️ [SERVICE] Plus de places disponibles pour le programme: {programme_id_int}")
                raise HTTPException(
                    status_code=400,
                    detail="Désolé, il n'y a plus de places disponibles pour ce programme"
                )

            # Vérifier les doublons
            print("🔍 [SERVICE] Vérification des doublons...")
            is_duplicate = await check_duplicate_preinscription(form_data.email, programme_id_int, session)
            if is_duplicate:
                raise HTTPException(
                    status_code=400,
                    detail="Une préinscription existe déjà pour cet email et ce programme"
                )

            # Générer un ID unique pour la préinscription
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            preinscription_id = f"preins_{programme_id_int}_{timestamp}"
            print(f"🆔 [SERVICE] ID de préinscription généré: {preinscription_id}")

            # Créer l'instance Preinscription pour la base de données
            preinscription_db = Preinscription(
                programme_id=programme_id_int,
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
                rgpd_consent_date=datetime.now().date(),
                date_soumission=datetime.now().date(),
                source="formulaire_web"
            )

            # Mettre à jour le nombre de places disponibles
            programme.places_disponibles -= 1
            print(f"✅ [SERVICE] Mise à jour des places disponibles: {programme.places_disponibles} restantes")
            
            # Sauvegarder la préinscription
            session.add(preinscription_db)
            await session.flush()
            print(f"💾 [SERVICE] Préinscription sauvegardée dans la base de données: {preinscription_id}")

            # Préparer les informations du programme pour la réponse
            programme_info = {
                "id": programme.id,
                "nom": programme.nom,
                "description": programme.description,
                "date_debut": programme.date_debut.isoformat() if programme.date_debut else None,
                "date_fin": programme.date_fin.isoformat() if programme.date_fin else None,
                "lieu": programme.lieu,
                "places_disponibles": programme.places_disponibles,
                "places_totales": programme.places_totales,
                "statut": programme.statut.value if programme.statut else None,
                "prix": programme.prix
            }

            # Créer un dossier pour les préinscriptions si nécessaire
            preinscriptions_dir = os.path.join(FICHIERS_DIR, "preinscriptions")
            os.makedirs(preinscriptions_dir, exist_ok=True)
            print(f"📁 [SERVICE] Dossier des préinscriptions: {preinscriptions_dir}")
            
            # Préparer les données à sauvegarder dans le fichier JSON
            preinscription_data = {
                "id": preinscription_id,
                "programme_id": programme_id,
                **form_data.model_dump()
            }
            print(f"📋 [SERVICE] Données de préinscription à sauvegarder: {preinscription_data}")
            
            # Sauvegarder les données dans un fichier JSON
            file_path = os.path.join(preinscriptions_dir, f"{preinscription_id}.json")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(preinscription_data, f, ensure_ascii=False, indent=2, default=serialize_dates)
                print(f"💾 [SERVICE] Fichier JSON créé: {file_path}")
            except Exception as file_error:
                print(f"💥 [SERVICE] Erreur lors de la sauvegarde du fichier JSON: {str(file_error)}")
                # Ne pas lever d'exception ici car les données sont déjà en base de données
            
            # Convertir les dates dans le résultat également
            result = {
                "id": preinscription_id,
                "status": "success",
                "message": "Préinscription enregistrée avec succès",
                "programme_info": programme_info
            }
            print(f"✅ [SERVICE] Préinscription traitée avec succès: {preinscription_id}")
            print(f"📊 [SERVICE] Résultat final: {result}")
            return result
        
    except Exception as e:
        print(f"💥 [SERVICE] Erreur lors du traitement de la préinscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de la préinscription: {str(e)}"
        )