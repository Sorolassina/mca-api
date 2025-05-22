from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, cast, String, text
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
from datetime import datetime
from io import BytesIO

from app.database import get_db
from app.services.emargement_service import EmargementService
from app.services.pdf_generator import SignaturePDFGenerator
from app.models.models import (
    BesoinEvenement, 
    Evenement, 
    Emargement, 
    Inscription,
    Programme
)
from app.schemas.forms.schema_emargement import (
    EmargementCreate,
    EmargementResponse,
    EmargementSignature,
    EmargementListResponse,
    EmargementCreateResponse
)
from app.core.exceptions import NotFoundException, ValidationError
from app.config import settings, get_base_url
from app.utils.transaction_utils import transaction_manager

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.post("/create", response_model=EmargementCreateResponse)
async def create_emargement_distant(
    emargement: EmargementCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Crée un nouvel émargement et retourne l'URL de signature appropriée"""
    print("\n" + "="*50)
    print("🎯 CRÉATION D'UN NOUVEL ÉMARGEMENT")
    print("="*50)
    print(f"📧 Email: {emargement.email}")
    print(f"📝 Mode signature: {emargement.mode_signature}")
    print(f"🌐 URL de la requête: {request.url}")
    print(f"👤 IP du client: {request.client.host}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔄 Début de la création...")
        response = await service.create_emargement(emargement)
        print("✅ Émargement créé avec succès")
        print(f"   📌 ID: {response['emargement']['id']}")
        print(f"   🔗 URL de signature: {response['signature_url']}")
        
        print("\n" + "="*50)
        print("✨ FIN CRÉATION ÉMARGEMENT")
        print("="*50 + "\n")
        
        return response
    except (NotFoundException, ValidationError) as e:
        print("\n❌ ERREUR: Création échouée")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get/{emargement_id}", response_model=EmargementResponse)
async def get_emargement(
    emargement_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Récupère un émargement par son ID"""
    print("\n" + "="*50)
    print("🎯 RÉCUPÉRATION D'UN ÉMARGEMENT")
    print("="*50)
    print(f"📌 ID Émargement: {emargement_id}")
    print(f"🌐 URL de la requête: {request.url}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔍 Recherche de l'émargement...")
        emargement = await service.get_emargement(emargement_id)
        print("✅ Émargement trouvé:")
        print(f"   📧 Email: {emargement.email}")
        print(f"   📝 Mode: {emargement.mode_signature}")
        print(f"   ✍️ Signé: {'Oui' if emargement.signature_image else 'Non'}")
        
        print("\n" + "="*50)
        print("✨ FIN RÉCUPÉRATION ÉMARGEMENT")
        print("="*50 + "\n")
        return emargement
    except NotFoundException as e:
        print("\n❌ ERREUR: Émargement non trouvé")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/list", response_model=EmargementListResponse)
async def list_emargements(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    inscription_id: Optional[int] = None,
    evenement_id: Optional[int] = None,
    statut: Optional[str] = None
):
    """
    Liste générale des émargements avec pagination et statistiques.
    
    Cette route est optimisée pour :
    - La pagination des résultats (skip/limit)
    - L'obtention de statistiques globales (total, validés, en attente)
    - Le filtrage flexible (par inscription, événement, statut)
    
    Paramètres:
    - skip: Nombre d'émargements à sauter (pour la pagination)
    - limit: Nombre maximum d'émargements à retourner
    - inscription_id: Filtrer par ID d'inscription
    - evenement_id: Filtrer par ID d'événement
    - statut: Filtrer par statut de signature
    
    Retourne:
    - emargements: Liste des émargements pour la page demandée
    - total: Nombre total d'émargements
    - validated: Nombre d'émargements validés
    - pending: Nombre d'émargements en attente
    """
    print("\n" + "="*50)
    print("📋 LISTE DES ÉMARGEMENTS")
    print("="*50)
    print(f"📊 Paramètres de pagination:")
    print(f"   - Skip: {skip}")
    print(f"   - Limit: {limit}")
    
    if inscription_id:
        print(f"🔍 Filtre par inscription: {inscription_id}")
    if evenement_id:
        print(f"🎯 Filtre par événement: {evenement_id}")
    if statut:
        print(f"📝 Filtre par statut: {statut}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔄 Récupération des émargements...")
        result = await service.get_emargements(
            skip=skip,
            limit=limit,
            inscription_id=inscription_id,
            evenement_id=evenement_id,
            statut=statut
        )
        
        print("\n✅ Résultats obtenus:")
        print(f"   📌 Total: {result['total']} émargements")
        print(f"   ✅ Validés: {result['validated']}")
        print(f"   ⏳ En attente: {result['pending']}")
        print(f"   📄 Retournés: {len(result['emargements'])} émargements")
        
        print("\n" + "="*50)
        print("✨ FIN LISTE ÉMARGEMENTS")
        print("="*50 + "\n")
        
        return result
        
    except Exception as e:
        print("\n❌ ERREUR lors de la récupération")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save/{emargement_id}/signature", response_model=EmargementResponse,include_in_schema=False)
async def save_signature(
    emargement_id: int,
    signature_data: EmargementSignature,
    request: Request,
    db: Session = Depends(get_db)
):
    """Sauvegarde la signature d'un émargement"""
    print("\n" + "="*50)
    print("🎯 SAUVEGARDE D'UNE SIGNATURE")
    print("="*50)
    print(f"📌 ID Émargement: {emargement_id}")
    print(f"🌐 URL de la requête: {request.url}")
    print(f"👤 IP du client: {request.client.host}")
    print(f"🖥️ User-Agent: {request.headers.get('user-agent', 'Non spécifié')}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔄 Début de la sauvegarde...")
        # Ajouter l'IP et le User-Agent automatiquement
        signature_data.ip_address = request.client.host
        signature_data.user_agent = request.headers.get("user-agent", "")
        print("✅ Données de signature enrichies avec IP et User-Agent")
        
        # Sauvegarder la signature
        print("📝 Sauvegarde de la signature en cours...")
        emargement = await service.save_signature(emargement_id, signature_data)
        print("✅ Signature sauvegardée avec succès")
        print(f"   📧 Email: {emargement.email}")
        print(f"   📅 Date: {emargement.date_signature}")
        
        print("\n" + "="*50)
        print("✨ FIN SAUVEGARDE SIGNATURE")
        print("="*50 + "\n")
        
        # Retourner directement l'émargement qui sera sérialisé selon EmargementResponse
        return emargement
        
    except (NotFoundException, ValidationError) as e:
        print("\n❌ ERREUR: Sauvegarde échouée")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/link/{emargement_id}/signature-link",include_in_schema=False)
async def generate_signature_link(
    emargement_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Génère un lien de signature pour un émargement"""
    print("\n" + "="*50)
    print("🎯 GÉNÉRATION D'UN LIEN DE SIGNATURE")
    print("="*50)
    print(f"📌 ID Émargement: {emargement_id}")
    print(f"🌐 URL de la requête: {request.url}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔑 Génération du token...")
        token = await service.generate_signature_token(emargement_id)
        base_url = get_base_url(request)
        signature_url = f"{base_url}/api-mca/v1/emargement/signature/{token}"
        
        print("✅ Lien de signature généré avec succès")
        print(f"   🔗 URL: {signature_url}")
        
        print("\n" + "="*50)
        print("✨ FIN GÉNÉRATION LIEN")
        print("="*50 + "\n")
        
        return {"signature_url": signature_url}
    except (NotFoundException, ValidationError) as e:
        print("\n❌ ERREUR: Génération du lien échouée")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/signature/{token}", response_class=HTMLResponse,include_in_schema=False)
async def signature_distant_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Page de signature à distance avec le formulaire de signature"""
    print("\n" + "="*50)
    print("🎯 DÉBUT TRAITEMENT SIGNATURE DISTANTE")
    print("="*50)
    print(f"🔑 Token reçu: {token[:20]}...")
    print(f"🌐 URL de la requête: {request.url}")
    print(f"👤 IP du client: {request.client.host}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔄 Début de la transaction")
        async with transaction_manager(db) as db:
            # Vérifier uniquement le token et récupérer l'émargement
            print("🔍 Vérification du token...")
            payload = await service.verify_signature_token(token)
            print(f"✅ Token vérifié - Payload: {payload}")
            
            print(f"\n🔍 Récupération de l'émargement {payload['emargement_id']}...")
            emargement = await service.get_emargement(payload["emargement_id"])
            print(f"✅ Émargement trouvé:")
            print(f"   📧 Email: {emargement.email}")
            print(f"   📝 Mode: {emargement.mode_signature}")
            
            # Vérifier que l'émargement n'est pas déjà signé
            if emargement.signature_image:
                print(f"\n⚠️ ATTENTION: Émargement déjà signé pour {emargement.email}")
                return templates.TemplateResponse(
                    "forms/signature_already_signed.html",
                    {
                        "request": request,
                        "emargement": emargement,
                        "email": emargement.email,
                        "config": {"MCA_WEBSITE_URL": settings.MCA_WEBSITE_URL}
                    }
                )

            # Récupérer l'événement uniquement pour l'affichage
            print(f"\n🔍 Récupération de l'événement {emargement.evenement_id}...")
            stmt = select(Evenement).where(Evenement.id == emargement.evenement_id)
            result = await db.execute(stmt)
            evenement = result.scalar_one_or_none()
            
            if not evenement:
                print(f"❌ ERREUR: Événement {emargement.evenement_id} non trouvé")
                raise NotFoundException(f"Événement {emargement.evenement_id} non trouvé")
                
            print(f"✅ Événement trouvé:")
            print(f"   📌 Titre: {evenement.titre}")
            print(f"   📅 Date: {evenement.date_debut}")

            print("\n📄 Préparation du template de signature...")
            response = templates.TemplateResponse(
                "forms/signature_distant.html",
                {
                    "request": request,
                    "emargement": emargement,
                    "email": emargement.email,
                    "evenement": evenement,
                    "token": token,
                    "config": {"MCA_WEBSITE_URL": settings.MCA_WEBSITE_URL},
                    "now": datetime.now()
                }
            )
            print("✅ Template préparé avec succès")
            print("\n" + "="*50)
            print("✨ FIN TRAITEMENT SIGNATURE DISTANTE")
            print("="*50 + "\n")
            return response

    except NotFoundException as e:
        print("\n❌ ERREUR: Émargement non trouvé")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        print("\n❌ ERREUR: Validation échouée")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("\n❌ ERREUR INATTENDUE")
        print(f"   📝 Type: {type(e).__name__}")
        print(f"   📝 Message: {str(e)}")
        print("\n📋 Traceback:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue")

@router.get("/signature/presentiel/{evenement_id}", response_class=HTMLResponse)
async def signature_presentiel_page(
    evenement_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Page de signature en présentiel avec la liste des inscrits au programme et la zone de signature"""
    print("\n" + "="*50)
    print("🎯 DÉBUT TRAITEMENT SIGNATURE PRÉSENTIEL")
    print("="*50)
    print(f"📌 ID Événement: {evenement_id}")
    print(f"🌐 URL de la requête: {request.url}")
    print(f"👤 IP du client: {request.client.host}")
    
    service = EmargementService(db, request)
    try:
        print("\n🔍 Récupération des données pour la signature en présentiel...")
        # Utiliser le service pour récupérer toutes les données nécessaires
        data = await service.get_presentiel_signature_data(evenement_id)
        
        print("\n📄 Préparation du template...")
        response = templates.TemplateResponse(
            "forms/signature_presentiel.html",
            {
                "request": request,
                "evenement": data["evenement"],
                "programme": data["programme"],
                "participants": data["participants"],
                "config": {"MCA_WEBSITE_URL": settings.MCA_WEBSITE_URL},
                "now": datetime.now()
            }
        )
        print("✅ Template préparé avec succès")
        
        print("\n" + "="*50)
        print("✨ FIN TRAITEMENT SIGNATURE PRÉSENTIEL")
        print("="*50 + "\n")
        return response
        
    except NotFoundException as e:
        print(f"\n❌ ERREUR: {str(e)}")
        print("="*50 + "\n")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue")

@router.get("/evenement/{evenement_id}/liste", response_model=List[dict])
async def get_emargements_evenement(
    evenement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Liste détaillée des émargements pour un événement spécifique.
    
    Cette route est optimisée pour :
    - L'affichage détaillé des émargements d'un événement spécifique
    - L'inclusion des informations complètes des inscriptions
    - La vérification du statut de participation et de remplissage des besoins
    
    Paramètres:
    - evenement_id: ID de l'événement dont on veut la liste des émargements
    
    Retourne une liste d'émargements avec pour chacun :
    - id: ID de l'émargement
    - nom: Nom du participant (si inscrit)
    - prenom: Prénom du participant (si inscrit)
    - email: Email du participant
    - date_signature: Date de signature
    - mode_signature: Mode de signature (distant/presentiel)
    - is_validated: Statut de validation
    - a_rempli_besoins: Indique si le participant a rempli ses besoins
    - is_participant: Indique si la personne est un participant officiel
    """
    print("\n" + "="*50)
    print(f"📋 LISTE DES ÉMARGEMENTS POUR L'ÉVÉNEMENT {evenement_id}")
    print("="*50)
    
    try:
        print("\n🔍 Vérification de l'existence de l'événement...")
        # Récupérer d'abord l'événement pour vérifier son existence
        res = await db.execute(select(Evenement).where(Evenement.id == evenement_id))
        evenement = res.scalar_one_or_none()
        if not evenement:
            print(f"❌ Événement {evenement_id} non trouvé")
            raise NotFoundException(f"Événement {evenement_id} non trouvé")
        print(f"✅ Événement trouvé: {evenement.titre}")
            
        print("\n📥 Récupération des émargements...")
        # Récupérer tous les émargements de l'événement
        res = await db.execute(select(Emargement).where(Emargement.evenement_id == evenement_id))
        emargements = res.scalars().all()
        print(f"✅ {len(emargements)} émargements trouvés")
        
        print("\n🔄 Traitement des émargements...")
        # Pour chaque émargement, chercher si on a des infos dans BesoinEvenement
        result = []
        for emargement in emargements:
            print(f"\n👤 Traitement de l'émargement pour {emargement.email}")
            # Recherche simple dans inscriptions pour obtenir le nom et prénom
            query = text("""
                SELECT nom, prenom
                FROM inscriptions
                WHERE email = :email
            """)
            res = await db.execute(
                query,
                {"email": emargement.email}
            )
            inscription = res.first()
            
            # Recherche séparée dans besoins_evenement
            query_besoins = text("""
                SELECT *
                FROM besoins_evenement
                WHERE CAST(event_id AS INTEGER) = :event_id
                AND email = :email
            """)
            res_besoins = await db.execute(
                query_besoins,
                {"event_id": evenement_id, "email": emargement.email}
            )
            besoin = res_besoins.first()
            
            if inscription:
                print(f"✅ Inscription trouvée pour {inscription.nom} {inscription.prenom}")
            else:
                print("ℹ️ Aucune inscription trouvée pour ce participant")
            
            if besoin:
                print("✅ Besoins trouvés pour ce participant")
            else:
                print("ℹ️ Aucun besoin trouvé pour ce participant")
            
            result.append({
                "id": emargement.id,
                "nom": inscription.nom if inscription else None,
                "prenom": inscription.prenom if inscription else None,
                "email": emargement.email,
                "date_signature": emargement.date_signature,
                "mode_signature": emargement.mode_signature,
                "is_validated": emargement.is_validated,
                "a_rempli_besoins": besoin is not None,
                "is_participant": besoin.is_participant if besoin else None
            })
            
        print("\n" + "="*50)
        print(f"✨ FIN LISTE ÉMARGEMENTS - {len(result)} participants traités")
        print("="*50 + "\n")
            
        return result
    except NotFoundException as e:
        print(f"\n❌ ERREUR: {str(e)}")
        print("="*50 + "\n")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/participant/{email}/liste", response_model=List[dict],include_in_schema=False)
async def get_emargements_participant(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère la liste des émargements d'un participant pour tous ses événements"""
    print("\n" + "="*50)
    print(f"📋 LISTE DES ÉMARGEMENTS POUR LE PARTICIPANT {email}")
    print("="*50)
    
    try:
        print("\n🔍 Récupération des émargements...")
        # Récupérer tous les émargements de cette personne
        res = await db.execute(
            select(Emargement).where(Emargement.email == email)
        )
        emargements = res.scalars().all()
        print(f"✅ {len(emargements)} émargements trouvés")
        
        result = []
        for emargement in emargements:
            print(f"\n👤 Traitement de l'émargement {emargement.id}...")
            # Récupérer l'événement
            res_evenement = await db.execute(
                select(Evenement).where(Evenement.id == emargement.evenement_id)
            )
            evenement = res_evenement.scalar_one_or_none()
            
            if evenement:  # Ne traiter que les événements qui existent encore
                print(f"✅ Événement trouvé: {evenement.titre}")
                
                # Recherche dans inscriptions pour le nom et prénom
                res_inscription = await db.execute(
                    text("SELECT nom, prenom FROM inscriptions WHERE email = :email"),
                    {"email": email}
                )
                inscription = res_inscription.first()
                
                # Chercher si on a des infos dans BesoinEvenement
                res_besoin = await db.execute(
                    text("""
                        SELECT * FROM besoins_evenement 
                        WHERE CAST(event_id AS INTEGER) = :event_id 
                        AND email = :email
                    """),
                    {"event_id": evenement.id, "email": email}
                )
                besoin = res_besoin.first()
                
                if inscription:
                    print(f"✅ Inscription trouvée pour {inscription.nom} {inscription.prenom}")
                if besoin:
                    print("✅ Besoins trouvés pour cet événement")
                
                result.append({
                    "id": emargement.id,
                    "evenement_id": evenement.id,
                    "titre": evenement.titre,
                    "date_debut": evenement.date_debut,
                    "date_fin": evenement.date_fin,
                    "lieu": evenement.lieu,
                    "nom": inscription.nom if inscription else None,
                    "prenom": inscription.prenom if inscription else None,
                    "date_signature": emargement.date_signature,
                    "mode_signature": emargement.mode_signature,
                    "is_validated": emargement.is_validated,
                    "a_rempli_besoins": besoin is not None,
                    "is_participant": besoin.is_participant if besoin else None
                })
        
        print("\n" + "="*50)
        print(f"✨ FIN LISTE ÉMARGEMENTS - {len(result)} événements traités")
        print("="*50 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/evenement/{evenement_id}/signatures-pdf",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "PDF des signatures généré avec succès",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        404: {"description": "Événement non trouvé"},
        500: {"description": "Erreur lors de la génération du PDF"}
    },
    summary="📄 Télécharger la liste des signatures",
    description="""
    Génère un PDF contenant la liste des participants avec leurs signatures pour un événement donné.
    
    Le PDF inclut :
    - Le titre de l'événement
    - La date de l'événement
    - La liste des participants avec leurs signatures
    - Le mode de signature (présentiel/distant)
    - La date de signature
    
    Le fichier est retourné en streaming pour une meilleure performance.
    """
)
async def generate_signatures_pdf(
    evenement_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Génère un PDF contenant la liste des participants avec leurs signatures pour un événement donné.
    Nécessite une authentification administrateur.
    """
    print("\n" + "="*50)
    print("🎯 GÉNÉRATION DU PDF DES SIGNATURES")
    print("="*50)
    print(f"📌 ID Événement: {evenement_id}")
    print(f"🌐 URL de la requête: {request.url}")
    
    try:
        # Récupérer l'événement
        stmt = select(Evenement).where(Evenement.id == evenement_id)
        result = await db.execute(stmt)
        evenement = result.scalar_one_or_none()
        if not evenement:
            raise HTTPException(
                status_code=404,
                detail="Événement non trouvé"
            )
        
        # Récupérer tous les émargements avec les informations d'inscription
        stmt = select(
            Emargement,
            Inscription.nom,
            Inscription.prenom
        ).outerjoin(
            Inscription,
            Emargement.email == Inscription.email
        ).where(
            Emargement.evenement_id == evenement_id
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        # Transformer les résultats pour inclure les noms et prénoms
        emargements = []
        for row in rows:
            emargement = row[0]
            emargement.nom = row[1]  # nom de l'inscription
            emargement.prenom = row[2]  # prénom de l'inscription
            emargements.append(emargement)
        
        print(f"\n📊 Statistiques:")
        print(f"   👥 Nombre de participants: {len(emargements)}")
        print(f"   ✍️ Signatures présentielles: {sum(1 for e in emargements if e.mode_signature == 'presentiel')}")
        print(f"   🌐 Signatures à distance: {sum(1 for e in emargements if e.mode_signature == 'distant')}")
        print(f"   ✅ Signatures validées: {sum(1 for e in emargements if e.is_validated)}")
        
        # Générer le PDF
        pdf_generator = SignaturePDFGenerator()
        pdf_buffer = pdf_generator.generate_signature_pdf(evenement, emargements)
        
        print("\n✅ PDF généré avec succès")
        print(f"   📄 Nombre de participants inclus: {len(emargements)}")
        
        print("\n" + "="*50)
        print("✨ FIN GÉNÉRATION PDF")
        print("="*50 + "\n")
        
        # Retourner le PDF en streaming
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="signatures_{evenement.titre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
            }
        )
        
    except Exception as e:
        print("\n❌ ERREUR: Génération du PDF échouée")
        print(f"   📝 Détail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
    











