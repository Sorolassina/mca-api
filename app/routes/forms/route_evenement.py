from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.evenement_service import EvenementService
from app.schemas.forms.schema_evenement import (
    EvenementCreate,
    EvenementUpdate,
    EvenementResponse
)
from app.core.exceptions import NotFoundException, ValidationError
import traceback
from contextlib import asynccontextmanager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@asynccontextmanager
async def route_transaction(db: AsyncSession):
    """Gestionnaire de contexte pour les transactions de route"""
    print("\n=== 🔄 DÉBUT TRANSACTION ROUTE ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    try:
        yield
    except Exception as e:
        print(f"❌ Erreur dans la transaction route: {str(e)}")
        if db.is_active:
            print("🔄 Rollback de la transaction route")
            await db.rollback()
        raise
    finally:
        print(f"📌 État final de la session route: {'active' if db.is_active else 'inactive'}")
        print("=== FIN TRANSACTION ROUTE ===\n")

@router.post("/create", response_model=EvenementResponse)
async def create_evenement(
    evenement: EvenementCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouvel événement"""
    print("\n=== 🎯 ROUTE: CRÉATION ÉVÉNEMENT ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        print(f"📥 Données reçues dans la route: {evenement.model_dump(exclude_none=True)}")
        
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.create_evenement(evenement)
            print(f"✅ Route: Événement créé avec succès: {result.id}")
        
        print("=== FIN ROUTE CRÉATION ===\n")
        return result
        
    except ValidationError as e:
        print(f"❌ Route: Erreur de validation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundException as e:
        print(f"❌ Route: Ressource non trouvée: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'événement: {str(e)}")

@router.get("/get/{evenement_id}", response_model=EvenementResponse)
async def get_evenement(
    evenement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Récupère un événement par son ID"""
    print(f"\n=== 🔍 ROUTE: RÉCUPÉRATION ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.get_evenement(evenement_id)
            print(f"✅ Route: Événement récupéré avec succès: {result.id}")
        
        print("=== FIN ROUTE RÉCUPÉRATION ===\n")
        return result
        
    except NotFoundException as e:
        print(f"❌ Route: Événement non trouvé: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'événement: {str(e)}")

@router.get("/search/title/{titre}", response_model=EvenementResponse)
async def get_evenement_by_title(
    titre: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère un événement par son titre (recherche insensible à la casse)"""
    print(f"\n=== 🔍 ROUTE: RECHERCHE ÉVÉNEMENT PAR TITRE '{titre}' ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.get_evenement_by_title(titre)
            print(f"✅ Route: Événement trouvé par titre: {result.id} - {result.titre}")
        
        print("=== FIN ROUTE RECHERCHE PAR TITRE ===\n")
        return result
        
    except NotFoundException as e:
        print(f"❌ Route: Événement non trouvé avec le titre '{titre}': {str(e)}")
        raise HTTPException(status_code=404, detail=f"Aucun événement trouvé avec le titre '{titre}'")
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche de l'événement: {str(e)}")

@router.get("/search/title/{titre}/participants", response_model=List[dict])
async def get_evenement_participants_by_title(
    titre: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les participants d'un événement par son titre"""
    print(f"\n=== 👥 ROUTE: RECHERCHE PARTICIPANTS PAR TITRE '{titre}' ===")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            evenement = await service.get_evenement_by_title(titre)
            participants = await service.get_participants(evenement.id)
            print(f"✅ Route: {len(participants)} participants trouvés pour l'événement '{titre}'")
        
        print("=== FIN ROUTE RECHERCHE PARTICIPANTS ===\n")
        return participants
        
    except NotFoundException as e:
        print(f"❌ Route: Événement non trouvé avec le titre '{titre}': {str(e)}")
        raise HTTPException(status_code=404, detail=f"Aucun événement trouvé avec le titre '{titre}'")
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche des participants: {str(e)}")

@router.get("/list", response_model=List[EvenementResponse])
async def list_evenements(
    skip: int = 0,
    limit: int = 100,
    statut: Optional[str] = None,
    type_evenement: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Liste les événements avec filtres optionnels"""
    service = EvenementService(db)
    return await service.get_evenements(
        skip=skip,
        limit=limit,
        statut=statut,
        type_evenement=type_evenement
    )

@router.put("/update/{evenement_id}", response_model=EvenementResponse)
async def update_evenement(
    evenement_id: int,
    evenement: EvenementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour un événement existant"""
    print(f"\n=== 🔄 ROUTE: MISE À JOUR ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        print(f"📥 Données de mise à jour reçues dans la route: {evenement.model_dump(exclude_none=True)}")
        
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.update_evenement(evenement_id, evenement)
            print(f"✅ Route: Événement mis à jour avec succès: {result.id}")
        
        print("=== FIN ROUTE MISE À JOUR ===\n")
        return result
        
    except ValidationError as e:
        print(f"❌ Route: Erreur de validation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundException as e:
        print(f"❌ Route: Ressource non trouvée: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour de l'événement: {str(e)}")

@router.delete("/delete/{evenement_id}")
async def delete_evenement(
    evenement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Supprime un événement"""
    print(f"\n=== 🗑️ ROUTE: SUPPRESSION ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            await service.delete_evenement(evenement_id)
            print(f"✅ Route: Événement {evenement_id} supprimé avec succès")
        
        print("=== FIN ROUTE SUPPRESSION ===\n")
        return {"message": "Événement supprimé avec succès"}
        
    except NotFoundException as e:
        print(f"❌ Route: Événement non trouvé: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de l'événement: {str(e)}")

@router.post("participant/add/{evenement_id}/{inscription_id}")
async def add_participant(
    evenement_id: int,
    inscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Ajoute un participant à un événement"""
    print(f"\n=== 👥 ROUTE: AJOUT PARTICIPANT À L'ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    print(f"📝 Données reçues: inscription_id={inscription_id}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            evenement = await service.add_participant(evenement_id, inscription_id)
            print(f"✅ Route: Participant {inscription_id} ajouté avec succès à l'événement {evenement_id}")
            print(f"📊 Nombre total de participants: {evenement.nombre_participants}")
        
        print("=== FIN ROUTE AJOUT PARTICIPANT ===\n")
        return {"message": "Participant ajouté avec succès", "evenement": evenement}
        
    except ValidationError as e:
        print(f"❌ Route: Erreur de validation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundException as e:
        print(f"❌ Route: Ressource non trouvée: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du participant: {str(e)}")

@router.delete("/participant/remove/{evenement_id}/{inscription_id}")
async def remove_participant(
    evenement_id: int,
    inscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retire un participant d'un événement"""
    print(f"\n=== 👥 ROUTE: RETRAIT PARTICIPANT DE L'ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    print(f"📝 Données reçues: inscription_id={inscription_id}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            evenement = await service.remove_participant(evenement_id, inscription_id)
            print(f"✅ Route: Participant {inscription_id} retiré avec succès de l'événement {evenement_id}")
            print(f"📊 Nombre total de participants: {evenement.nombre_participants}")
        
        print("=== FIN ROUTE RETRAIT PARTICIPANT ===\n")
        return {"message": "Participant retiré avec succès", "evenement": evenement}
        
    except ValidationError as e:
        print(f"❌ Route: Erreur de validation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundException as e:
        print(f"❌ Route: Ressource non trouvée: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du retrait du participant: {str(e)}")

@router.get("/participant/get/{evenement_id}", response_model=List[dict])
async def get_participants(
    evenement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Récupère la liste des participants d'un événement"""
    print(f"\n=== 👥 ROUTE: RÉCUPÉRATION PARTICIPANTS DE L'ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.get_participants(evenement_id)
            print(f"✅ Route: {len(result)} participants trouvés pour l'événement {evenement_id}")
            for participant in result:
                print(f"  - {participant['nom']} {participant['prenom']} ({participant['email']})")
        
        print("=== FIN ROUTE RÉCUPÉRATION PARTICIPANTS ===\n")
        return result
        
    except NotFoundException as e:
        print(f"❌ Route: Événement non trouvé: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des participants: {str(e)}")

@router.put("/statut/update/{evenement_id}/{nouveau_statut}")
async def update_statut(
    evenement_id: int,
    nouveau_statut: str,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour le statut d'un événement"""
    print(f"\n=== 🔄 ROUTE: MISE À JOUR STATUT DE L'ÉVÉNEMENT {evenement_id} ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    print(f"📝 Nouveau statut: {nouveau_statut}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            evenement = await service.update_statut(evenement_id, nouveau_statut)
            print(f"✅ Route: Statut mis à jour avec succès pour l'événement {evenement_id}")
            print(f"📊 Nouveau statut: {evenement.statut}")
            print(f"📊 État de l'événement:")
            print(f"  - En cours: {evenement.est_en_cours}")
            print(f"  - Terminé: {evenement.est_termine}")
        
        print("=== FIN ROUTE MISE À JOUR STATUT ===\n")
        return {"message": "Statut mis à jour avec succès", "evenement": evenement}
        
    except ValidationError as e:
        print(f"❌ Route: Erreur de validation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundException as e:
        print(f"❌ Route: Ressource non trouvée: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du statut: {str(e)}")

@router.get("/a-venir", response_model=List[EvenementResponse])
async def get_evenements_a_venir(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les événements à venir"""
    print("\n=== 📅 ROUTE: RÉCUPÉRATION ÉVÉNEMENTS À VENIR ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.get_evenements_a_venir(limit)
            print(f"✅ Route: {len(result)} événements à venir trouvés")
            for event in result:
                print(f"  - {event.titre} (ID: {event.id}, Date: {event.date_debut})")
        
        print("=== FIN ROUTE ÉVÉNEMENTS À VENIR ===\n")
        return result
        
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des événements à venir: {str(e)}")

@router.get("/en-cours", response_model=List[EvenementResponse])
async def get_evenements_en_cours(
    db: AsyncSession = Depends(get_db)
):
    """Récupère les événements en cours"""
    print("\n=== 🎯 ROUTE: RÉCUPÉRATION ÉVÉNEMENTS EN COURS ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.get_evenements_en_cours()
            print(f"✅ Route: {len(result)} événements en cours trouvés")
            for event in result:
                print(f"  - {event.titre} (ID: {event.id}, Date: {event.date_debut} - {event.date_fin})")
        
        print("=== FIN ROUTE ÉVÉNEMENTS EN COURS ===\n")
        return result
        
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des événements en cours: {str(e)}")

@router.get("/termines", response_model=List[EvenementResponse])
async def get_evenements_termines(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les événements terminés"""
    print("\n=== ✅ ROUTE: RÉCUPÉRATION ÉVÉNEMENTS TERMINÉS ===")
    print(f"📌 État initial de la session route: {'active' if db.is_active else 'inactive'}")
    
    try:
        async with route_transaction(db):
            service = EvenementService(db)
            result = await service.get_evenements_termines(limit)
            print(f"✅ Route: {len(result)} événements terminés trouvés")
            for event in result:
                print(f"  - {event.titre} (ID: {event.id}, Date fin: {event.date_fin})")
        
        print("=== FIN ROUTE ÉVÉNEMENTS TERMINÉS ===\n")
        return result
        
    except Exception as e:
        print(f"❌ Route: Erreur inattendue: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des événements terminés: {str(e)}") 