# app/routes/route_programme.py
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schema_programme import (
    ProgrammeCreate,
    ProgrammeUpdate,
    ProgrammeResponse,
    ProgrammeBase
)
from app.services.service_programme import ProgrammeService
from app.database import get_db
from datetime import datetime
from typing import List
from app.config import TEMPLATE_DIR, get_static_url
from app.core.logging_config import setup_logging
import traceback

# Configuration du logger
logger = setup_logging().getChild('routes.programme')

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)
# Ajouter la fonction get_static_url aux templates
templates.env.globals["get_static_url"] = get_static_url

# Route API pour lister tous les programmes (JSON)
@router.get("/liste", response_model=List[ProgrammeResponse])
async def list_programmes_api(db: AsyncSession = Depends(get_db)):
    """Retourne la liste de tous les programmes en JSON"""
    print("\n=== 📋 DÉBUT LISTE PROGRAMMES API ===")
    try:
        print("🔍 Initialisation du service...")
        service = ProgrammeService(db)
        
        print("📊 Récupération des programmes...")
        programmes = await service.get_all_programmes()
        
        print(f"\n✅ Liste des programmes récupérée:")
        print(f"  - Nombre total: {len(programmes)}")
        for prog in programmes:
            print(f"  - Programme {prog.id}: {prog.nom} ({prog.statut})")
        
        print("=== FIN LISTE PROGRAMMES API ===\n")
        return programmes
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la liste:")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise

# Route pour créer un programme
@router.post("/create", response_model=ProgrammeResponse)
async def create_programme(
    programme: ProgrammeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau programme"""
    print("\n=== 📝 DÉBUT CRÉATION PROGRAMME API ===")
    try:
        print("📋 Données reçues:")
        print(f"  - Nom: {programme.nom}")
        print(f"  - Statut: {programme.statut}")
        print(f"  - Places: {programme.places_disponibles}/{programme.places_totales}")
        print(f"  - Objectifs: {len(programme.objectifs) if programme.objectifs else 0}")
        print(f"  - Prérequis: {len(programme.prerequis) if programme.prerequis else 0}")
        
        print("\n🔍 Initialisation du service...")
        service = ProgrammeService(db)
        
        print("📊 Création du programme...")
        nouveau_programme = await service.create_programme(programme)
        
        print(f"\n✅ Programme créé avec succès:")
        print(f"  - ID: {nouveau_programme.id}")
        print(f"  - Nom: {nouveau_programme.nom}")
        print(f"  - Statut: {nouveau_programme.statut}")
        print(f"  - Places: {nouveau_programme.places_disponibles}/{nouveau_programme.places_totales}")
        
        print("=== FIN CRÉATION PROGRAMME API ===\n")
        return nouveau_programme
        
    except Exception as e:
        print(f"❌ Erreur lors de la création:")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise

# Route pour obtenir un programme spécifique
@router.get("/get/{programme_id}", response_model=ProgrammeResponse)
async def get_programme(
    programme_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Récupère un programme par son ID"""
    print(f"\n=== 🔍 DÉBUT RÉCUPÉRATION PROGRAMME {programme_id} API ===")
    try:
        print("🔍 Initialisation du service...")
        service = ProgrammeService(db)
        
        print(f"📊 Récupération du programme {programme_id}...")
        programme = await service.get_programme(programme_id)
        
        print(f"\n✅ Programme trouvé:")
        print(f"  - ID: {programme.id}")
        print(f"  - Nom: {programme.nom}")
        print(f"  - Statut: {programme.statut}")
        print(f"  - Places: {programme.places_disponibles}/{programme.places_totales}")
        print(f"  - Objectifs: {len(programme.objectifs)}")
        print(f"  - Prérequis: {len(programme.prerequis)}")
        
        print("=== FIN RÉCUPÉRATION PROGRAMME API ===\n")
        return programme
        
    except HTTPException as he:
        print(f"⚠️ Programme non trouvé: ID={programme_id}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la récupération:")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise

# Route pour mettre à jour un programme
@router.put("/update/{programme_id}", response_model=ProgrammeResponse)
async def update_programme(
    programme_id: int,
    programme: ProgrammeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour un programme existant"""
    print(f"\n=== 🔄 DÉBUT MISE À JOUR PROGRAMME {programme_id} API ===")
    try:
        print("📋 Données de mise à jour reçues:")
        update_data = programme.model_dump(exclude_unset=True)
        print(f"  - Champs à mettre à jour: {list(update_data.keys())}")
        if 'objectifs' in update_data:
            print(f"  - Nombre d'objectifs: {len(update_data['objectifs'])}")
        if 'prerequis' in update_data:
            print(f"  - Nombre de prérequis: {len(update_data['prerequis'])}")
        
        print("\n🔍 Initialisation du service...")
        service = ProgrammeService(db)
        
        print(f"📊 Mise à jour du programme {programme_id}...")
        programme_mis_a_jour = await service.update_programme(programme_id, programme)
        
        print(f"\n✅ Programme mis à jour avec succès:")
        print(f"  - ID: {programme_mis_a_jour.id}")
        print(f"  - Nom: {programme_mis_a_jour.nom}")
        print(f"  - Statut: {programme_mis_a_jour.statut}")
        print(f"  - Places: {programme_mis_a_jour.places_disponibles}/{programme_mis_a_jour.places_totales}")
        print(f"  - Objectifs: {len(programme_mis_a_jour.objectifs)}")
        print(f"  - Prérequis: {len(programme_mis_a_jour.prerequis)}")
        
        print("=== FIN MISE À JOUR PROGRAMME API ===\n")
        return programme_mis_a_jour
        
    except HTTPException as he:
        print(f"⚠️ Erreur HTTP: {str(he)}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour:")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise

# Route pour supprimer un programme
@router.delete("/delete/{programme_id}", response_model=dict)
async def delete_programme(programme_id: int, db: AsyncSession = Depends(get_db)):
    """Supprime un programme par son ID"""
    print(f"\n=== 🗑️ DÉBUT SUPPRESSION PROGRAMME {programme_id} API ===")
    try:
        print("🔍 Initialisation du service...")
        service = ProgrammeService(db)
        print(f"📊 Suppression du programme {programme_id}...")
        
        result = await service.delete_programme(programme_id)
        
        if result:
            print(f"\n✅ Programme supprimé avec succès:")
            print(f"  - ID: {programme_id}")
            return {"message": f"Programme {programme_id} supprimé avec succès"}
        else:
            raise HTTPException(
                status_code=500,
                detail="La suppression a échoué"
            )
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression:")
        print(f"📋 Traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Route pour obtenir les détails d'un programme (JSON)
@router.get("/details/{programme_id}", response_model=ProgrammeResponse)
async def get_programme_details(
    programme_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'un programme en JSON"""
    print(f"\n=== 🔍 DÉBUT RÉCUPÉRATION DÉTAILS PROGRAMME {programme_id} ===")
    try:
        print("🔍 Initialisation du service...")
        service = ProgrammeService(db)
        
        print(f"📊 Récupération des détails du programme {programme_id}...")
        programme = await service.get_programme(programme_id)
        
        print(f"\n✅ Détails récupérés:")
        print(f"  - ID: {programme.id}")
        print(f"  - Nom: {programme.nom}")
        print(f"  - Statut: {programme.statut}")
        print(f"  - Places: {programme.places_disponibles}/{programme.places_totales}")
        print(f"  - Objectifs: {len(programme.objectifs)}")
        print(f"  - Prérequis: {len(programme.prerequis)}")
        
        print("=== FIN RÉCUPÉRATION DÉTAILS PROGRAMME ===\n")
        return programme
        
    except HTTPException as he:
        print(f"⚠️ Programme non trouvé: ID={programme_id}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des détails:")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise