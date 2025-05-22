# app/services/service_programme.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from sqlalchemy.orm import selectinload
from app.schemas.schema_programme import (
    ProgrammeCreate,
    ProgrammeUpdate,
    ProgrammeResponse,
    ProgrammeBase,
    StatutProgramme
)
from app.models.models import (
    Programme as ProgrammeModel,
    ProgrammePrerequis,
    ProgrammeObjectif,
    Preinscription,
    Inscription
)
from typing import List, Optional
from datetime import date, datetime
import uuid
from app.core.logging_config import setup_logging
from app.utils.transaction_utils import transaction_manager
import traceback
from app.utils.sequence_utils import diagnose_sequence, reset_sequence
from app.utils.date_convertUTC import ensure_utc
from sqlalchemy import func

# Configuration du logger
logger = setup_logging().getChild('programme')

class ProgrammeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        print(f"🚀 Initialisation du service ProgrammeService avec session {id(db)}")
        print(f"📌 État initial de la session: {'active' if self.db.is_active else 'inactive'}")

    async def _get_programme_by_id(self, programme_id: int, raise_if_not_found: bool = False) -> Optional[ProgrammeModel]:
        """Méthode utilitaire pour récupérer un programme par son ID
        
        Args:
            programme_id: ID du programme à récupérer
            raise_if_not_found: Si True, lève une HTTPException si le programme n'existe pas
        """
        print(f"\n=== 🔍 RECHERCHE PROGRAMME {programme_id} ===")
        try:
            query = select(ProgrammeModel).options(
                selectinload(ProgrammeModel.prerequis),
                selectinload(ProgrammeModel.objectifs)
            ).where(ProgrammeModel.id == programme_id)
            
            print("🔎 Exécution de la requête...")
            result = await self.db.execute(query)
            programme = result.scalar_one_or_none()
            
            if programme:
                print(f"✅ Programme trouvé:")
                print(f"  - ID: {programme.id}")
                print(f"  - Nom: {programme.nom}")
                print(f"  - Statut: {programme.statut}")
                print(f"  - Nombre d'objectifs: {len(programme.objectifs)}")
                print(f"  - Nombre de prérequis: {len(programme.prerequis)}")
            else:
                print(f"❌ Programme {programme_id} non trouvé")
                if raise_if_not_found:
                    raise HTTPException(status_code=404, detail="Programme non trouvé")
            
            print("=== FIN RECHERCHE PROGRAMME ===\n")
            return programme
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def _convert_to_response(self, programme: ProgrammeModel, prerequis: List[str] = None, objectifs: List[str] = None) -> ProgrammeResponse:
        """Méthode utilitaire pour convertir un modèle en réponse"""
        print(f"\n=== 🔄 CONVERSION PROGRAMME {programme.id} EN RÉPONSE ===")
        try:
            print(f"📝 Données du programme à convertir:")
            print(f"  - ID: {programme.id}")
            print(f"  - Nom: {programme.nom}")
            print(f"  - Statut: {programme.statut}")
            print(f"  - Places: {programme.places_disponibles}/{programme.places_totales}")
            
            # Récupérer le nombre d'inscriptions (depuis la table inscriptions)
            query_inscriptions = select(func.count()).select_from(Inscription).where(
                Inscription.programme_id == programme.id
            )
            result_inscriptions = await self.db.execute(query_inscriptions)
            nombre_inscriptions = result_inscriptions.scalar() or 0
            
            # Récupérer le nombre de préinscriptions (depuis la table preinscriptions)
            query_preinscriptions = select(func.count()).select_from(Preinscription).where(
                Preinscription.programme_id == programme.id
            )
            result_preinscriptions = await self.db.execute(query_preinscriptions)
            nombre_preinscriptions = result_preinscriptions.scalar() or 0
            
            # Calculer les taux
            taux_remplissage = (nombre_inscriptions / programme.places_totales * 100) if programme.places_totales > 0 else 0
            taux_conversion = (nombre_inscriptions / nombre_preinscriptions * 100) if nombre_preinscriptions > 0 else 0
            
            print(f"  - Nombre d'inscriptions: {nombre_inscriptions}")
            print(f"  - Nombre de préinscriptions: {nombre_preinscriptions}")
            print(f"  - Taux de remplissage: {taux_remplissage:.1f}%")
            print(f"  - Taux de conversion: {taux_conversion:.1f}%")
            
            programme_dict = {
                "id": programme.id,
                "nom": programme.nom,
                "description": programme.description,
                "date_debut": programme.date_debut,
                "date_fin": programme.date_fin,
                "lieu": programme.lieu,
                "places_disponibles": programme.places_disponibles,
                "places_totales": programme.places_totales,
                "statut": programme.statut,
                "prix": programme.prix,
                "created_at": programme.created_at,
                "updated_at": programme.updated_at,
                "prerequis": prerequis if prerequis is not None else [],
                "objectifs": objectifs if objectifs is not None else [],
                "nombre_inscriptions": nombre_inscriptions,
                "nombre_preinscriptions": nombre_preinscriptions,
                "taux_remplissage": round(taux_remplissage, 1),
                "taux_conversion": round(taux_conversion, 1)
            }
            
            print("\n📊 Données converties:")
            print(f"  - Nombre de prérequis: {len(programme_dict['prerequis'])}")
            print(f"  - Nombre d'objectifs: {len(programme_dict['objectifs'])}")
            print(f"  - Statistiques:")
            print(f"    * Inscriptions: {programme_dict['nombre_inscriptions']}")
            print(f"    * Préinscriptions: {programme_dict['nombre_preinscriptions']}")
            print(f"    * Taux de remplissage: {programme_dict['taux_remplissage']}%")
            print(f"    * Taux de conversion: {programme_dict['taux_conversion']}%")
            
            response = ProgrammeResponse(**programme_dict)
            print("✅ Conversion réussie")
            print("=== FIN CONVERSION PROGRAMME ===\n")
            return response
            
        except Exception as e:
            print(f"❌ Erreur lors de la conversion: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def create_programme(self, programme: ProgrammeCreate) -> ProgrammeResponse:
        """Crée un nouveau programme avec ses objectifs et prérequis"""
        print("\n=== DÉBUT CRÉATION PROGRAMME ===")
        
        try:
            print(f"📝 Données reçues:")
            print(f"  - Nom: {programme.nom}")
            print(f"  - Statut: {programme.statut}")
            print(f"  - Places: {programme.places_disponibles}/{programme.places_totales}")
            print(f"  - Nombre d'objectifs: {len(programme.objectifs) if programme.objectifs else 0}")
            print(f"  - Nombre de prérequis: {len(programme.prerequis) if programme.prerequis else 0}")
            
            # Convertir les dates en UTC
            date_debut = await ensure_utc(programme.date_debut)
            date_fin = await ensure_utc(programme.date_fin)

            # Diagnostic de la séquence avant la création
            diagnosis = await diagnose_sequence(self.db, "programmes")
            if not diagnosis["is_healthy"]:
                print("⚠️ Séquence non saine détectée, tentative de réinitialisation...")
                await reset_sequence(self.db, "programmes")

            async with transaction_manager(self.db) as db:
                # Création du programme
                db_programme = ProgrammeModel(
                    nom=programme.nom,
                    description=programme.description,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    lieu=programme.lieu,
                    places_disponibles=programme.places_disponibles,
                    places_totales=programme.places_totales,
                    statut=programme.statut,
                    prix=programme.prix
                )
                db.add(db_programme)
                print(f"📦 Objet Programme créé en mémoire: {db_programme}")
                print("➕ Programme ajouté à la session")
                print(f"📌 État de la session après ajout: {'active' if db.is_active else 'inactive'}")

                await db.flush()
                print(f"✅ Programme créé en base: ID={db_programme.id}")

                # Création des objectifs
                objectifs_list = []
                if programme.objectifs:
                    print("\n📋 Création des objectifs:")
                    for ordre, objectif in enumerate(programme.objectifs, 1):
                        db_objectif = ProgrammeObjectif(
                            programme_id=db_programme.id,
                            objectif=objectif,
                            ordre=ordre
                        )
                        db.add(db_objectif)
                        await db.flush()
                        objectifs_list.append(objectif)
                        print(f"  ✅ Objectif {ordre}: {objectif[:50]}...")
                    print(f"📊 Total: {len(programme.objectifs)} objectifs créés")

                # Création des prérequis
                prerequis_list = []
                if programme.prerequis:
                    print("\n📋 Création des prérequis:")
                    for prerequis in programme.prerequis:
                        db_prerequis = ProgrammePrerequis(
                            programme_id=db_programme.id,
                            prerequis=prerequis
                        )
                        db.add(db_prerequis)
                        await db.flush()
                        prerequis_list.append(prerequis)
                        print(f"  ✅ Prérequis: {prerequis[:50]}...")
                    print(f"📊 Total: {len(programme.prerequis)} prérequis créés")

                # Vérification des relations avant la fin de la transaction
                print("\n📊 Vérification des relations:")
                print(f"  - Nombre de prérequis: {len(prerequis_list)}")
                print(f"  - Nombre d'objectifs: {len(objectifs_list)}")
                print(f"\n🎉 PROGRAMME CRÉÉ AVEC SUCCÈS: ID={db_programme.id}")
                print("=== FIN CRÉATION PROGRAMME ===\n")

                # Récupération du programme complet pour la réponse
                return await self._convert_to_response(db_programme, prerequis_list, objectifs_list)
            
        except Exception as e:
            print(f"❌ Erreur lors de la création: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_programme(self, programme_id: int) -> ProgrammeResponse:
        """Récupère un programme par son ID avec ses objectifs et prérequis"""
        print(f"\n=== 🔍 DÉBUT RÉCUPÉRATION PROGRAMME {programme_id} ===")
        try:
            # Utilise _get_programme_by_id avec raise_if_not_found=True
            programme = await self._get_programme_by_id(programme_id, raise_if_not_found=True)
            
            print("\n🔄 Conversion en réponse...")
            # Préparation des listes d'objectifs et prérequis
            objectifs_list = [o.objectif for o in sorted(programme.objectifs, key=lambda x: x.ordre)]
            prerequis_list = [p.prerequis for p in programme.prerequis]
            
            response = await self._convert_to_response(programme, prerequis_list, objectifs_list)
            
            print("=== FIN RÉCUPÉRATION PROGRAMME ===\n")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_all_programmes(self) -> List[ProgrammeResponse]:
        """Récupère tous les programmes avec leurs objectifs et prérequis"""
        print("\n=== 📋 DÉBUT RÉCUPÉRATION TOUS LES PROGRAMMES ===")
        try:
            print("🔎 Exécution de la requête...")
            query = select(ProgrammeModel).options(
                selectinload(ProgrammeModel.objectifs),
                selectinload(ProgrammeModel.prerequis)
            )
            result = await self.db.execute(query)
            programmes = result.scalars().all()
            
            print(f"\n✅ Programmes trouvés: {len(programmes)}")
            for prog in programmes:
                print(f"  - Programme {prog.id}:")
                print(f"    * Nom: {prog.nom}")
                print(f"    * Statut: {prog.statut}")
                print(f"    * Places: {prog.places_disponibles}/{prog.places_totales}")
                print(f"    * Objectifs: {len(prog.objectifs)}")
                print(f"    * Prérequis: {len(prog.prerequis)}")
            
            print("\n🔄 Conversion des programmes en réponses...")
            responses = []
            for programme in programmes:
                # Préparation des listes d'objectifs et prérequis pour chaque programme
                objectifs_list = [o.objectif for o in sorted(programme.objectifs, key=lambda x: x.ordre)]
                prerequis_list = [p.prerequis for p in programme.prerequis]
                
                # Conversion avec les listes préparées
                response = await self._convert_to_response(programme, prerequis_list, objectifs_list)
                responses.append(response)
            
            print("=== FIN RÉCUPÉRATION TOUS LES PROGRAMMES ===\n")
            return responses
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def update_programme(self, programme_id: int, programme: ProgrammeUpdate) -> ProgrammeResponse:
        """Met à jour un programme existant"""
        print(f"\n=== 🔄 DÉBUT MISE À JOUR PROGRAMME {programme_id} ===")
        try:
            print(f"📝 Données de mise à jour reçues:")
            update_data = programme.model_dump(exclude_unset=True)
            print(f"  - Champs à mettre à jour: {list(update_data.keys())}")
            if 'objectifs' in update_data:
                print(f"  - Nombre d'objectifs: {len(update_data['objectifs'])}")
            if 'prerequis' in update_data:
                print(f"  - Nombre de prérequis: {len(update_data['prerequis'])}")

            async with transaction_manager(self.db) as db:
                # Utilise _get_programme_by_id avec raise_if_not_found=True
                db_programme = await self._get_programme_by_id(programme_id, raise_if_not_found=True)
                
                print(f"\n📊 État actuel du programme:")
                print(f"  - Nom: {db_programme.nom}")
                print(f"  - Statut: {db_programme.statut}")
                print(f"  - Places: {db_programme.places_disponibles}/{db_programme.places_totales}")
                print(f"  - Objectifs: {len(db_programme.objectifs)}")
                print(f"  - Prérequis: {len(db_programme.prerequis)}")

                # Séparation des champs de base et des relations
                base_fields = {k: v for k, v in update_data.items() 
                             if k not in {'id', 'created_at', 'updated_at', 'prerequis', 'objectifs'}}
                
                # Mise à jour des champs de base
                if base_fields:
                    print("\n📝 Mise à jour des champs de base:")
                    for key, value in base_fields.items():
                        old_value = getattr(db_programme, key)
                        setattr(db_programme, key, value)
                        print(f"  - {key}: {old_value} -> {value}")
                    print("✅ Champs de base mis à jour")

                # Mise à jour des objectifs
                if 'objectifs' in update_data:
                    print("\n📝 Mise à jour des objectifs:")
                    print(f"  - Ancien nombre: {len(db_programme.objectifs)}")
                    print(f"  - Nouveau nombre: {len(update_data['objectifs'])}")
                    
                    # Suppression des anciens objectifs
                    stmt = delete(ProgrammeObjectif).where(ProgrammeObjectif.programme_id == programme_id)
                    await db.execute(stmt)
                    print("  ✅ Anciens objectifs supprimés")
                    
                    # Ajout des nouveaux objectifs
                    db_programme.objectifs = []
                    for ordre, objectif in enumerate(update_data['objectifs'], 1):
                        db_objectif = ProgrammeObjectif(
                            programme_id=programme_id,
                            objectif=objectif,
                            ordre=ordre
                        )
                        db.add(db_objectif)
                        db_programme.objectifs.append(db_objectif)
                        print(f"  ✅ Objectif {ordre} ajouté")
                    print("✅ Nouveaux objectifs ajoutés")

                # Mise à jour des prérequis
                if 'prerequis' in update_data:
                    print("\n📝 Mise à jour des prérequis:")
                    print(f"  - Ancien nombre: {len(db_programme.prerequis)}")
                    print(f"  - Nouveau nombre: {len(update_data['prerequis'])}")
                    
                    # Suppression des anciens prérequis
                    stmt = delete(ProgrammePrerequis).where(ProgrammePrerequis.programme_id == programme_id)
                    await db.execute(stmt)
                    print("  ✅ Anciens prérequis supprimés")
                    
                    # Ajout des nouveaux prérequis
                    db_programme.prerequis = []
                    for prerequis in update_data['prerequis']:
                        db_prerequis = ProgrammePrerequis(
                            programme_id=programme_id,
                            prerequis=prerequis
                        )
                        db.add(db_prerequis)
                        db_programme.prerequis.append(db_prerequis)
                        print(f"  ✅ Prérequis ajouté")
                    print("✅ Nouveaux prérequis ajoutés")

            print(f"\n🎉 PROGRAMME MIS À JOUR AVEC SUCCÈS: ID={programme_id}")
            print("=== FIN MISE À JOUR PROGRAMME ===\n")
            
            return await self.get_programme(programme_id)
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def delete_programme(self, programme_id: int) -> bool:
        """Supprime un programme et toutes ses relations."""
        try:
            async with transaction_manager(self.db) as db:
                # Récupérer le programme avec ses relations
                programme = await self._get_programme_by_id(programme_id, raise_if_not_found=True)
                if not programme:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Programme avec l'ID {programme_id} non trouvé"
                    )

                print(f"\n🗑️ Suppression du programme {programme_id}:")
                print(f"📋 Nom: {programme.nom}")

                # Supprimer d'abord les objectifs
                if programme.objectifs:
                    print("\n📋 Suppression des objectifs:")
                    for objectif in programme.objectifs:
                        await db.delete(objectif)
                        print(f"  ✅ Objectif supprimé: {objectif.objectif[:50]}...")
                    await db.flush()
                    print(f"📊 Total: {len(programme.objectifs)} objectifs supprimés")

                # Supprimer ensuite les prérequis
                if programme.prerequis:
                    print("\n📋 Suppression des prérequis:")
                    for prerequis in programme.prerequis:
                        await db.delete(prerequis)
                        print(f"  ✅ Prérequis supprimé: {prerequis.prerequis[:50]}...")
                    await db.flush()
                    print(f"📊 Total: {len(programme.prerequis)} prérequis supprimés")

                # Enfin, supprimer le programme
                await db.delete(programme)
                await db.flush()
                print("\n✅ Programme supprimé avec succès")
                print("=== FIN DE LA SUPPRESSION ===\n")
                return True

        except Exception as e:
            print(f"\n❌ Erreur lors de la suppression:")
            print(f"📋 Traceback:")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la suppression du programme: {str(e)}"
            )

    async def update_statut(self, programme_id: int, nouveau_statut: str) -> ProgrammeResponse:
        """Met à jour le statut d'un programme"""
        print(f"\n=== 🔄 DÉBUT MISE À JOUR STATUT PROGRAMME {programme_id} ===")
        try:
            print(f"📝 Nouveau statut demandé: {nouveau_statut}")
            
            async with transaction_manager(self.db) as db:
                # Récupération du programme
                db_programme = await self._get_programme_by_id(programme_id)
                if not db_programme:
                    print(f"❌ Programme {programme_id} non trouvé")
                    raise HTTPException(status_code=404, detail="Programme non trouvé")
                
                print(f"\n📊 État actuel:")
                print(f"  - Statut actuel: {db_programme.statut}")
                print(f"  - Places: {db_programme.places_disponibles}/{db_programme.places_totales}")
                
                # Validation du nouveau statut
                if nouveau_statut not in [s.value for s in StatutProgramme]:
                    print(f"❌ Statut invalide: {nouveau_statut}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Statut invalide. Statuts valides: {[s.value for s in StatutProgramme]}"
                    )
                
                # Mise à jour du statut
                ancien_statut = db_programme.statut
                db_programme.statut = nouveau_statut
                print(f"✅ Statut mis à jour: {ancien_statut} -> {nouveau_statut}")

            print(f"\n🎉 STATUT MIS À JOUR AVEC SUCCÈS: ID={programme_id}")
            print("=== FIN MISE À JOUR STATUT ===\n")
            
            return await self.get_programme(programme_id)
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du statut: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

# La création de l'instance se fera dans les routes avec la session DB