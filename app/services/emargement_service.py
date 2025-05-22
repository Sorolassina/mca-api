from typing import List, Optional
from datetime import datetime, timedelta
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import traceback
from app.models.models import Emargement,Inscription,Evenement
from app.schemas.forms.schema_emargement import EmargementCreate, EmargementSignature
from app.config import settings, get_base_url
from app.core.exceptions import NotFoundException, ValidationError
from app.utils.transaction_utils import transaction_manager
from app.utils.sequence_utils import diagnose_sequence, reset_sequence
from fastapi import Request
from app.services.email_service import EmailService

class EmargementService:
    def __init__(self, db: AsyncSession, request: Request):
        self.db = db
        self.request = request
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.token_expire_minutes = 30
        self.email_service = EmailService()
        print(f"🚀 Initialisation du service EmargementService avec session {id(db)}")
        print(f"📌 État initial de la session: {'active' if self.db.is_active else 'inactive'}")

    async def create_emargement(self, emargement: EmargementCreate) -> dict:
        """Crée un nouvel émargement et retourne les informations pour la signature"""
        print("\n=== 📝 DÉBUT CRÉATION ÉMARGEMENT ===")
        try:
            print(f"📋 Données reçues:")
            print(f"  - Événement ID: {emargement.evenement_id}")
            print(f"  - Mode signature: {emargement.mode_signature}")
            print(f"  - Email: {emargement.email}")

            async with transaction_manager(self.db) as db:
                # Diagnostic de la séquence avant traitement
                print("\n🔍 Diagnostic de la séquence avant traitement...")
                sequence_diagnostic = await diagnose_sequence(db, "emargements")
                print(f"📊 État de la séquence: {sequence_diagnostic}")

                # 1. Vérifier si l'événement existe
                result = await db.execute(
                    select(Evenement).filter(Evenement.id == emargement.evenement_id)
                )
                evenement = result.scalar_one_or_none()
                if not evenement:
                    print(f"❌ Événement {emargement.evenement_id} non trouvé")
                    raise NotFoundException(f"Événement avec l'ID {emargement.evenement_id} non trouvé")

                # 2. Vérifier que l'événement appartient à un programme
                if evenement.id_prog is None:
                    print("❌ L'événement n'est pas associé à un programme")
                    raise ValidationError("L'événement doit être associé à un programme")

                # 3. Vérifier que l'email appartient au programme
                # Si id_prog = 0, on vérifie que l'email appartient à n'importe quel programme
                if evenement.id_prog == 0:
                    result = await db.execute(
                        select(Inscription).filter(
                            Inscription.email == emargement.email
                        )
                    )
                else:
                    result = await db.execute(
                        select(Inscription).filter(
                            Inscription.programme_id == evenement.id_prog,
                            Inscription.email == emargement.email
                        )
                    )
                inscription = result.scalar_one_or_none()
                if not inscription:
                    if evenement.id_prog == 0:
                        print(f"❌ Aucune inscription trouvée pour l'email {emargement.email} dans aucun programme")
                        raise ValidationError("Cette personne n'est inscrite à aucun programme")
                    else:
                        print(f"❌ Aucune inscription trouvée pour l'email {emargement.email} dans le programme {evenement.id_prog}")
                        raise ValidationError("Cette personne n'est pas inscrite au programme associé à cet événement")

                # 4. Vérifier si un émargement existe déjà pour cet email et cet événement
                result = await db.execute(
                    select(Emargement).filter(
                        Emargement.evenement_id == emargement.evenement_id,
                        Emargement.email == emargement.email,
                        Emargement.signature_image != ""  # Vérifier si l'émargement a été signé
                    )
                )
                existing_emargement = result.scalar_one_or_none()
                if existing_emargement:
                    print("❌ Un émargement signé existe déjà pour cet email et cet événement")
                    raise ValidationError("Un émargement signé existe déjà pour cet email et cet événement")

                # Si un émargement non signé existe, on le supprime
                result = await db.execute(
                    select(Emargement).filter(
                        Emargement.evenement_id == emargement.evenement_id,
                        Emargement.email == emargement.email,
                        Emargement.signature_image == ""
                    )
                )
                old_emargement = result.scalar_one_or_none()
                if old_emargement:
                    print(f"🗑️ Suppression de l'ancien émargement non signé (ID: {old_emargement.id})")
                    await db.delete(old_emargement)
                    await db.flush()

                # Création de l'émargement
                db_emargement = Emargement(
                    evenement_id=emargement.evenement_id,
                    mode_signature=emargement.mode_signature,
                    email=emargement.email,
                    signature_image="",  # Explicitement définir une chaîne vide
                    is_validated=False
                )
                db.add(db_emargement)
                await db.flush()
                print(f"✅ Émargement créé: ID={db_emargement.id}")

                # Vérification de la séquence après traitement
                print("\n🔍 Diagnostic de la séquence après traitement...")
                sequence_diagnostic = await diagnose_sequence(db, "emargements")
                if not sequence_diagnostic["is_healthy"]:
                    print("\n⚠️ Séquence désynchronisée détectée, réinitialisation...")
                    await reset_sequence(db, "emargements")
                    print("✅ Séquence réinitialisée")

                # Préparer la réponse
                response = {
                    "emargement": {
                        "id": db_emargement.id,
                        "mode_signature": db_emargement.mode_signature,
                        "email": db_emargement.email,
                        "date_signature": db_emargement.date_signature,
                        "is_validated": db_emargement.is_validated
                    },
                    "signature_url": None,
                    "message": None
                }

                # Si mode distant, générer l'URL de signature
                if db_emargement.mode_signature == "distant":
                    token = await self.generate_signature_token(db_emargement.id)
                    base_url = get_base_url(self.request)
                    signature_url = f"{base_url}/api-mca/v1/emargement/signature/{token}"
                    response["signature_url"] = signature_url
                    response["message"] = "Voici votre lien de signature. Il est valable pendant 30 minutes."
                else:
                    response["message"] = "Veuillez vous présenter pour signer l'émargement."

            print("=== FIN CRÉATION ÉMARGEMENT ===\n")
            return response

        except Exception as e:
            print(f"❌ Erreur lors de la création: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_emargement(self, emargement_id: int) -> Emargement:
        """Récupère un émargement par son ID"""
        print(f"\n=== 🔍 DÉBUT RÉCUPÉRATION ÉMARGEMENT {emargement_id} ===")
        try:
            async with transaction_manager(self.db) as db:
                result = await db.execute(
                    select(Emargement).filter(Emargement.id == emargement_id)
                )
                emargement = result.scalar_one_or_none()
                
                if not emargement:
                    print(f"❌ Émargement {emargement_id} non trouvé")
                    raise NotFoundException(f"Émargement avec l'ID {emargement_id} non trouvé")
                
                print(f"✅ Émargement trouvé:")
                print(f"  - ID: {emargement.id}")
                print(f"  - Email: {emargement.email}")
                print(f"  - Mode signature: {emargement.mode_signature}")
                print(f"  - Date signature: {emargement.date_signature}")
                print(f"  - Signature: {'Présente' if emargement.signature_image else 'Absente'}")
                print(f"  - Validé: {'Oui' if emargement.is_validated else 'Non'}")

            print("=== FIN RÉCUPÉRATION ÉMARGEMENT ===\n")
            return emargement

        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_emargements(
        self,
        skip: int = 0,
        limit: int = 100,
        inscription_id: Optional[int] = None,
        evenement_id: Optional[int] = None,
        statut: Optional[str] = None
    ) -> dict:
        """Récupère la liste des émargements avec filtres optionnels"""
        print("\n=== 🔍 DÉBUT RÉCUPÉRATION LISTE ÉMARGEMENTS ===")
        try:
            # Construire la requête de base
            stmt = select(Emargement)
            print(f"📊 Requête initiale créée")

            # Appliquer les filtres
            if inscription_id:
                stmt = stmt.filter(Emargement.inscription_id == inscription_id)
                print(f"🔍 Filtre inscription_id appliqué: {inscription_id}")
            if evenement_id:
                stmt = stmt.filter(Emargement.evenement_id == evenement_id)
                print(f"🔍 Filtre evenement_id appliqué: {evenement_id}")
            if statut:
                stmt = stmt.filter(Emargement.statut == statut)
                print(f"🔍 Filtre statut appliqué: {statut}")

            # Récupérer tous les émargements pour le comptage total
            total_stmt = stmt
            total_result = await self.db.execute(total_stmt)
            total = len(total_result.scalars().all())
            print(f"📌 Nombre total d'émargements trouvés: {total}")
            
            if total == 0:
                print("⚠️ Aucun émargement trouvé avec les filtres actuels")
                return {
                    "emargements": [],
                    "total": 0,
                    "validated": 0,
                    "pending": 0
                }
            
            # Récupérer les émargements validés et en attente
            validated_stmt = stmt.filter(Emargement.is_validated == True)
            pending_stmt = stmt.filter(Emargement.is_validated == False)
            
            validated_result = await self.db.execute(validated_stmt)
            pending_result = await self.db.execute(pending_stmt)
            
            validated = len(validated_result.scalars().all())
            pending = len(pending_result.scalars().all())
            
            print(f"✅ Émargements validés: {validated}")
            print(f"⏳ Émargements en attente: {pending}")
            
            # Récupérer la page demandée
            print(f"\n📄 Récupération de la page (skip={skip}, limit={limit})...")
            stmt = stmt.offset(skip).limit(limit)
            result = await self.db.execute(stmt)
            emargements = result.scalars().all()
            print(f"📦 {len(emargements)} émargements récupérés pour cette page")
            
            # Afficher quelques détails sur les émargements récupérés
            if emargements:
                print("\n📋 Aperçu des émargements:")
                for em in emargements[:3]:  # Afficher les 3 premiers
                    print(f"   - ID: {em.id}, Email: {em.email}, Validé: {em.is_validated}")
                if len(emargements) > 3:
                    print(f"   ... et {len(emargements)-3} autres")
            
            response = {
                "emargements": emargements,
                "total": total,
                "validated": validated,
                "pending": pending
            }
            
            print("\n=== ✨ FIN RÉCUPÉRATION LISTE ÉMARGEMENTS ===\n")
            return response
            
        except Exception as e:
            print(f"\n❌ ERREUR lors de la récupération des émargements:")
            print(f"   📝 Type: {type(e).__name__}")
            print(f"   📝 Message: {str(e)}")
            print(f"   📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def generate_signature_token(self, emargement_id: int, mode: str = "distant") -> str:
        """Génère un token JWT pour la signature
        
        Args:
            emargement_id: ID de l'émargement
            mode: Mode de signature ('distant' ou 'presentiel')
            
        Returns:
            str: Token JWT généré
            
        Raises:
            ValidationError: Si l'émargement n'existe pas ou a déjà été signé
        """
        emargement = await self.get_emargement(emargement_id)
        
        if mode == "distant" and emargement.mode_signature != "distant":
            raise ValidationError("Le mode de signature doit être 'distant' pour générer un token distant")

        if emargement.is_validated or emargement.signature_image:
            raise ValidationError("L'émargement a déjà été signé et validé")

        # Créer le payload du token
        payload = {
            "emargement_id": emargement.id,
            "email": emargement.email,
            "evenement_id": emargement.evenement_id,
            "mode": mode,
            "exp": datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        }

        # Générer le token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        print(f"✅ Token généré pour l'émargement {emargement_id} en mode {mode}")
        return token

    async def verify_signature_token(self, token: str, expected_mode: str = None) -> dict:
        """Vérifie et décode un token de signature
        
        Args:
            token: Token JWT à vérifier
            expected_mode: Mode de signature attendu ('distant' ou 'presentiel')
            
        Returns:
            dict: Payload du token décodé
            
        Raises:
            ValidationError: Si le token est invalide ou expiré
        """
        print(f"🔑 [DEBUG] Token reçu pour vérification : {token}")
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            print(f"✅ [DEBUG] Payload décodé : {payload}")
            
            # Vérifier le mode si spécifié
            if expected_mode and payload.get("mode") != expected_mode:
                print(f"❌ [ERREUR] Mode de signature invalide : attendu {expected_mode}, reçu {payload.get('mode')}")
                raise ValidationError(f"Mode de signature invalide : attendu {expected_mode}")
                
            return payload
        except jwt.ExpiredSignatureError:
            print("⏰ [ERREUR] Le lien de signature a expiré !")
            raise ValidationError("Le lien de signature a expiré")
        except jwt.InvalidTokenError as e:
            print(f"❌ [ERREUR] Token de signature invalide : {e}")
            raise ValidationError("Token de signature invalide")

    async def save_signature(self, emargement_id: int, signature_data: EmargementSignature) -> Emargement:
        """Sauvegarde la signature d'un émargement"""
        print(f"\n=== ✍️ DÉBUT SAUVEGARDE SIGNATURE ÉMARGEMENT {emargement_id} ===")
        try:
            async with transaction_manager(self.db) as db:
                # Diagnostic de la séquence avant traitement
                print("\n🔍 Diagnostic de la séquence avant traitement...")
                sequence_diagnostic = await diagnose_sequence(db, "emargements")
                print(f"📊 État de la séquence: {sequence_diagnostic}")

                # Récupération de l'émargement
                result = await db.execute(
                    select(Emargement).filter(Emargement.id == emargement_id)
                )
                emargement = result.scalar_one_or_none()
                
                if not emargement:
                    print(f"❌ Émargement {emargement_id} non trouvé")
                    raise NotFoundException(f"Émargement avec l'ID {emargement_id} non trouvé")

                if emargement.signature_image:  # Si une signature existe déjà
                    print(f"❌ Une signature existe déjà pour cet émargement")
                    raise ValidationError("Une signature existe déjà pour cet émargement")

                # Si c'est une signature à distance, vérifier le token
                if emargement.mode_signature == "distant":
                    if not signature_data.token:
                        print("❌ Token manquant pour une signature à distance")
                        raise ValidationError("Token requis pour une signature à distance")
                    payload = await self.verify_signature_token(signature_data.token, expected_mode="distant")
                    if payload["emargement_id"] != emargement_id:
                        print("❌ Token invalide pour cet émargement")
                        raise ValidationError("Token invalide pour cet émargement")

                # Sauvegarder la signature et la photo
                emargement.signature_image = signature_data.signature_image
                if emargement.mode_signature == "distant" and signature_data.photo_profil:
                    emargement.photo_profil = signature_data.photo_profil
                emargement.date_signature = datetime.now()
                emargement.ip_address = signature_data.ip_address if emargement.mode_signature == "distant" else None
                emargement.user_agent = signature_data.user_agent if emargement.mode_signature == "distant" else None
                emargement.is_validated = True if emargement.mode_signature == "presentiel" else False
                
                db.add(emargement)
                await db.flush()
                print(f"✅ Signature et photo sauvegardées pour l'émargement {emargement_id}")

                # Vérification de la séquence après traitement
                print("\n🔍 Diagnostic de la séquence après traitement...")
                sequence_diagnostic = await diagnose_sequence(db, "emargements")
                if not sequence_diagnostic["is_healthy"]:
                    print("\n⚠️ Séquence désynchronisée détectée, réinitialisation...")
                    await reset_sequence(db, "emargements")
                    print("✅ Séquence réinitialisée")

            print("=== FIN SAUVEGARDE SIGNATURE ===\n")
            return emargement

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de la signature: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_emargements_evenement(self, evenement_id: int) -> List[dict]:
        """Récupère tous les émargements d'un événement avec les détails des inscriptions"""
        print("\n=== 🔍 DÉBUT RÉCUPÉRATION ÉMARGEMENTS ÉVÉNEMENT ===")
        try:
            async with transaction_manager(self.db) as db:
                # Récupérer tous les émargements de l'événement
                stmt = select(Emargement).where(Emargement.evenement_id == evenement_id)
                result = await db.execute(stmt)
                emargements = result.scalars().all()
                print(f"📋 {len(emargements)} émargements trouvés pour l'événement {evenement_id}")

                result = []
                for em in emargements:
                    # Récupérer l'inscription correspondante
                    stmt = select(Inscription).where(Inscription.email == em.email)
                    inscription_result = await db.execute(stmt)
                    inscription = inscription_result.scalar_one_or_none()
                    
                    if inscription:
                        result.append({
                            "id": em.id,
                            "inscription": {
                                "id": inscription.id,
                                "nom": inscription.nom,
                                "prenom": inscription.prenom,
                                "email": inscription.email
                            },
                            "mode_signature": em.mode_signature,
                            "date_signature": em.date_signature,
                            "signature": em.signature_image != "",
                            "is_validated": em.is_validated
                        })
                
                print(f"✅ {len(result)} émargements avec inscriptions trouvés")
                print("=== FIN RÉCUPÉRATION ÉMARGEMENTS ÉVÉNEMENT ===\n")
                return result
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des émargements: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_emargements_inscription(self, inscription_id: int) -> List[dict]:
        """Récupère tous les émargements d'une inscription avec les détails des événements"""
        print("\n=== 🔍 DÉBUT RÉCUPÉRATION ÉMARGEMENTS INSCRIPTION ===")
        try:
            async with transaction_manager(self.db) as db:
                # Récupérer l'inscription
                stmt = select(Inscription).where(Inscription.id == inscription_id)
                result = await db.execute(stmt)
                inscription = result.scalar_one_or_none()
                
                if not inscription:
                    print(f"❌ Inscription {inscription_id} non trouvée")
                    raise NotFoundException(f"Inscription avec l'ID {inscription_id} non trouvée")
                print(f"✅ Inscription trouvée pour {inscription.email}")

                # Récupérer tous les émargements de cette inscription
                stmt = select(Emargement).where(Emargement.email == inscription.email)
                result = await db.execute(stmt)
                emargements = result.scalars().all()
                print(f"📋 {len(emargements)} émargements trouvés pour cette inscription")

                result = []
                for em in emargements:
                    # Récupérer l'événement correspondant
                    stmt = select(Evenement).where(Evenement.id == em.evenement_id)
                    evenement_result = await db.execute(stmt)
                    evenement = evenement_result.scalar_one_or_none()
                    
                    if evenement:
                        result.append({
                            "id": em.id,
                            "evenement": {
                                "id": evenement.id,
                                "titre": evenement.titre,
                                "date_debut": evenement.date_debut,
                                "date_fin": evenement.date_fin
                            },
                            "mode_signature": em.mode_signature,
                            "date_signature": em.date_signature,
                            "signature": em.signature_image != "",
                            "is_validated": em.is_validated
                        })
                
                print(f"✅ {len(result)} émargements avec événements trouvés")
                print("=== FIN RÉCUPÉRATION ÉMARGEMENTS INSCRIPTION ===\n")
                return result
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des émargements: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_presentiel_signature_data(self, evenement_id: int) -> dict:
        """
        Récupère toutes les données nécessaires pour la page de signature en présentiel.
        Crée automatiquement les émargements pour tous les participants inscrits au programme.
        
        Args:
            evenement_id: ID de l'événement
            
        Returns:
            dict contenant:
                - evenement: L'événement
                - programme: Le programme associé
                - participants: Liste des participants inscrits avec leur statut de signature
                
        Raises:
            NotFoundException: Si l'événement ou le programme n'est pas trouvé
        """
        print("\n=== 🔍 DÉBUT RÉCUPÉRATION DONNÉES SIGNATURE PRÉSENTIEL ===")
        try:
            async with transaction_manager(self.db) as db:
                print("\n🔍 Récupération de l'événement et du programme...")
                # Récupérer l'événement et son programme associé avec chargement explicite de la relation
                stmt = select(Evenement).options(selectinload(Evenement.programme)).where(Evenement.id == evenement_id)
                result = await db.execute(stmt)
                evenement = result.scalar_one_or_none()
                
                if not evenement:
                    print(f"❌ Événement {evenement_id} non trouvé")
                    raise NotFoundException(f"Événement {evenement_id} non trouvé")
                print(f"✅ Événement trouvé: {evenement.titre}")
                    
                if not evenement.programme:
                    print("❌ L'événement n'est pas associé à un programme")
                    raise NotFoundException("Cet événement n'est pas associé à un programme")
                    
                # Récupérer le programme
                programme = evenement.programme
                print(f"✅ Programme trouvé: {programme.nom}")
                    
                print("\n👥 Récupération des inscriptions au programme...")
                # Récupérer toutes les inscriptions au programme
                stmt = select(Inscription).where(Inscription.programme_id == programme.id)
                result = await db.execute(stmt)
                inscriptions_programme = result.scalars().all()
                print(f"📋 {len(inscriptions_programme)} inscriptions trouvées")
                
                print("\n📝 Récupération des émargements existants...")
                # Récupérer tous les émargements existants pour cet événement
                stmt = select(Emargement).where(Emargement.evenement_id == evenement_id)
                result = await db.execute(stmt)
                emargements = result.scalars().all()
                print(f"📋 {len(emargements)} émargements trouvés")
                
                print("\n🔄 Création des émargements manquants...")
                # Créer un émargement pour chaque inscription qui n'en a pas
                for inscription in inscriptions_programme:
                    # Vérifier si un émargement existe déjà pour cet email
                    emargement_existant = next(
                        (e for e in emargements if e.email == inscription.email),
                        None
                    )
                    
                    if not emargement_existant:
                        print(f"📝 Création d'un émargement pour {inscription.email}")
                        nouvel_emargement = Emargement(
                            evenement_id=evenement_id,
                            mode_signature="presentiel",
                            email=inscription.email,
                            signature_image="",
                            is_validated=False
                        )
                        db.add(nouvel_emargement)
                        await db.flush()
                        emargements.append(nouvel_emargement)
                        print(f"✅ Émargement créé avec l'ID: {nouvel_emargement.id}")
                
                print("\n🔄 Préparation de la liste des participants...")
                # Préparer la liste des inscrits au programme avec leur statut de signature
                participants_list = []
                for inscription in inscriptions_programme:
                    # Chercher l'émargement correspondant
                    emargement = next(
                        (e for e in emargements if e.email == inscription.email),
                        None
                    )
                    
                    # Déterminer le statut de signature
                    a_signé = emargement is not None and emargement.signature_image
                    est_validé = emargement is not None and emargement.is_validated
                    
                    # Déterminer l'emoji et le statut visuel
                    if a_signé:
                        if est_validé:
                            emoji = "✅"  # Coche verte pour signature validée
                            statut = "validé"
                        else:
                            emoji = "⏳"  # Sablier pour signature en attente de validation
                            statut = "en_attente"
                    else:
                        emoji = "❌"  # Croix rouge pour non signé
                        statut = "non_signé"
                    
                    participants_list.append({
                        "id": inscription.id,
                        "nom": inscription.nom,
                        "prenom": inscription.prenom,
                        "email": inscription.email,
                        "a_signé": a_signé,
                        "est_validé": est_validé,
                        "emoji": emoji,
                        "statut": statut,
                        "emargement_id": emargement.id,  # Maintenant toujours présent
                        "date_signature": emargement.date_signature if emargement else None
                    })
                print(f"✅ {len(participants_list)} participants inscrits listés")
                
                print("\n=== ✨ FIN RÉCUPÉRATION DONNÉES SIGNATURE PRÉSENTIEL ===\n")
                return {
                    "evenement": evenement,
                    "programme": programme,
                    "participants": participants_list
                }
                
        except Exception as e:
            print(f"\n❌ ERREUR lors de la récupération des données:")
            print(f"   📝 Type: {type(e).__name__}")
            print(f"   📝 Message: {str(e)}")
            print(f"   📋 Traceback:\n{traceback.format_exc()}")
            raise 