from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func, text
from datetime import datetime, timezone
import traceback
from contextlib import asynccontextmanager

from app.models.models import Evenement
from app.schemas.forms.schema_evenement import EvenementCreate, EvenementUpdate, EvenementInscription
from app.core.exceptions import NotFoundException, ValidationError
from app.utils.sequence_utils import diagnose_sequence, reset_sequence
from app.utils.transaction_utils import transaction_manager
from app.utils.date_convertUTC import ensure_utc
from app.models.models import StatutEvenement

class EvenementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        print(f"🚀 Initialisation du service EvenementService avec session {id(db)}")
        print(f"📌 État initial de la session: {'active' if self.db.is_active else 'inactive'}")

    async def _determine_statut(self, date_debut: datetime, date_fin: datetime, statut_actuel: str = None) -> str:
        """Détermine automatiquement le statut d'un événement en fonction des dates"""
        # Assurer que toutes les dates sont en UTC
        now = datetime.now(timezone.utc)
        date_debut = await ensure_utc(date_debut)
        date_fin = await ensure_utc(date_fin)
        
        print(f"📅 Comparaison des dates:")
        print(f"  - Maintenant (UTC): {now}")
        print(f"  - Date début (UTC): {date_debut}")
        print(f"  - Date fin (UTC): {date_fin}")
        
        # Si l'événement est annulé, on garde ce statut
        if statut_actuel == "annule":
            return "annule"
            
        # Sinon, on détermine le statut en fonction des dates
        if now < date_debut:
            return "planifie"
        elif date_debut <= now <= date_fin:
            return "en_cours"
        else:  # now > date_fin
            return "termine"

    async def create_evenement(self, evenement: EvenementCreate) -> Evenement:
        """Crée un nouvel événement"""
        print("\n=== 🎯 DÉBUT CRÉATION ÉVÉNEMENT ===")
        try:
            # Diagnostic de la séquence avant la création pour surveiller les trous avec les id
            diagnosis = await diagnose_sequence(self.db, "evenements")
            if not diagnosis["is_healthy"]:
                print("⚠️ Séquence non saine détectée, tentative de réinitialisation...")
                await reset_sequence(self.db, "evenements")
            
            print(f"📝 Données reçues: {evenement.model_dump(exclude_none=True)}")
            print(f"📌 État de la session avant création: {'active' if self.db.is_active else 'inactive'}")
            
            # Conversion des dates en UTC avec logs détaillés
            print("\n🔄 Conversion des dates en UTC:")
            print("Date de début:")
            date_debut = await ensure_utc(evenement.date_debut)
            print("\nDate de fin:")
            date_fin = await ensure_utc(evenement.date_fin)
            
            # Validation des dates
            if date_debut >= date_fin:
                print("❌ Erreur: date_debut doit être antérieure à date_fin")
                print(f"  - Date début (UTC): {date_debut}")
                print(f"  - Date fin (UTC): {date_fin}")
                raise ValidationError("La date de début doit être antérieure à la date de fin")
            
            # Déterminer le statut automatiquement
            statut = await self._determine_statut(date_debut, date_fin)
            print(f"📊 Statut déterminé automatiquement: {statut}")
            
            async with transaction_manager(self.db) as db:
                # Création de l'objet Evenement avec les dates en UTC
                db_evenement = Evenement(
                    titre=evenement.titre,
                    description=evenement.description,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    lieu=evenement.lieu,
                    type_evenement=evenement.type_evenement,
                    statut=statut,
                    capacite_max=evenement.capacite_max,
                    animateur=evenement.animateur,
                    id_prog=evenement.id_prog
                )
                print(f"📦 Objet Evenement créé en mémoire: {db_evenement}")
                
                # Ajout à la session
                db.add(db_evenement)
                print("➕ Événement ajouté à la session")
                print(f"📌 État de la session après ajout: {'active' if db.is_active else 'inactive'}")
            
            # Après la transaction
            print(f"📌 État de la session après transaction: {'active' if self.db.is_active else 'inactive'}")
            
            # Rafraîchir l'objet dans une nouvelle transaction
            async with transaction_manager(self.db) as db:
                await db.refresh(db_evenement)
                print(f"🔄 Événement rafraîchi après commit: {db_evenement}")
                
                # Vérification des relations
                print("\n📊 Vérification des relations:")
                print(f"  - Nombre de besoins: {len(db_evenement.besoins)}")
                print(f"  - Nombre d'émargements: {len(db_evenement.emargements)}")
            
            print(f"\n🎉 ÉVÉNEMENT CRÉÉ AVEC SUCCÈS: {db_evenement.id}")
            print("=== FIN CRÉATION ÉVÉNEMENT ===\n")
            return db_evenement
            
        except ValidationError as ve:
            print(f"❌ Erreur de validation: {str(ve)}")
            raise
        except Exception as e:
            print(f"❌ Erreur inattendue lors de la création: {str(e)}")
            print(f"📋 Traceback complet:\n{traceback.format_exc()}")
            raise

    async def get_evenement(self, evenement_id: int) -> Evenement:
        """Récupère un événement par son ID"""
        print(f"\n=== 🔍 DÉBUT RÉCUPÉRATION ÉVÉNEMENT {evenement_id} ===")
        try:
            print(f"📌 État de la session: {'active' if self.db.is_active else 'inactive'}")
            print(f"🔎 Exécution de la requête pour l'événement {evenement_id}")
            
            async with transaction_manager(self.db) as db:
                result = await db.execute(
                    select(Evenement).filter(Evenement.id == evenement_id)
                )
                evenement = result.scalar_one_or_none()
                
                if not evenement:
                    print(f"❌ Événement {evenement_id} non trouvé")
                    raise NotFoundException(f"Événement avec l'ID {evenement_id} non trouvé")
                
                print(f"✅ Événement trouvé: {evenement}")
                print("\n📊 Relations:")
                print(f"  - Nombre de besoins: {len(evenement.besoins)}")
                print(f"  - Nombre d'émargements: {len(evenement.emargements)}")
                
                # Affichage des détails des besoins
                if evenement.besoins:
                    print("\n📋 Détails des besoins:")
                    for besoin in evenement.besoins:
                        print(f"  - Besoin {besoin.id}: {besoin.titre}")
                
                # Affichage des détails des émargements
                if evenement.emargements:
                    print("\n📋 Détails des émargements:")
                    for emargement in evenement.emargements:
                        print(f"  - Émargement {emargement.id}: {emargement.date_signature}")
            
            print(f"\n=== FIN RÉCUPÉRATION ÉVÉNEMENT {evenement_id} ===\n")
            return evenement
            
        except NotFoundException:
            raise
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_evenement_by_title(self, titre: str) -> Evenement:
        """Récupère un événement par son titre (recherche insensible à la casse)"""
        print(f"\n=== 🔍 DÉBUT RECHERCHE ÉVÉNEMENT PAR TITRE '{titre}' ===")
        try:
            print(f"📌 État de la session: {'active' if self.db.is_active else 'inactive'}")
            print(f"🔎 Exécution de la requête pour le titre '{titre}'")
            
            async with transaction_manager(self.db) as db:
                # Recherche insensible à la casse avec ILIKE (PostgreSQL) ou LIKE (SQLite)
                result = await db.execute(
                    select(Evenement).filter(func.lower(Evenement.titre) == titre.lower())
                )
                evenement = result.scalar_one_or_none()
                
                if not evenement:
                    print(f"❌ Événement avec le titre '{titre}' non trouvé")
                    raise NotFoundException(f"Événement avec le titre '{titre}' non trouvé")
                
                print(f"✅ Événement trouvé par titre: {evenement.id} - {evenement.titre}")
                print("\n📊 Relations:")
                print(f"  - Nombre de besoins: {len(evenement.besoins)}")
                print(f"  - Nombre d'émargements: {len(evenement.emargements)}")
            
            print(f"\n=== FIN RECHERCHE ÉVÉNEMENT PAR TITRE '{titre}' ===\n")
            return evenement
            
        except NotFoundException:
            raise
        except Exception as e:
            print(f"❌ Erreur lors de la recherche par titre: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_evenements(
        self,
        skip: int = 0,
        limit: int = 100,
        statut: Optional[str] = None,
        type_evenement: Optional[str] = None,
        date_debut: Optional[datetime] = None,
        date_fin: Optional[datetime] = None
    ) -> List[Evenement]:
        """Récupère la liste des événements avec filtres optionnels"""
        query = select(Evenement)

        if statut:
            query = query.filter(Evenement.statut == statut)
        if type_evenement:
            query = query.filter(Evenement.type_evenement == type_evenement)
        if date_debut:
            query = query.filter(Evenement.date_debut >= date_debut)
        if date_fin:
            query = query.filter(Evenement.date_fin <= date_fin)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_evenement(self, evenement_id: int, evenement: EvenementUpdate) -> Evenement:
        """Met à jour un événement existant"""
        print(f"\n=== 🔄 DÉBUT MISE À JOUR ÉVÉNEMENT {evenement_id} ===")
        try:
            print(f"📝 Données de mise à jour reçues: {evenement.model_dump(exclude_none=True)}")
            print(f"📌 État de la session avant mise à jour: {'active' if self.db.is_active else 'inactive'}")
            
            async with transaction_manager(self.db) as db:
                # Récupération de l'événement
                print(f"🔍 Recherche de l'événement {evenement_id}...")
                result = await db.execute(
                    select(Evenement).filter(Evenement.id == evenement_id)
                )
                db_evenement = result.scalar_one_or_none()
                
                if not db_evenement:
                    print(f"❌ Événement {evenement_id} non trouvé")
                    raise NotFoundException(f"Événement avec l'ID {evenement_id} non trouvé")
                
                print(f"✅ Événement trouvé avant mise à jour: {db_evenement}")
                print(f"📊 Valeurs actuelles:")
                print(f"  - titre: {db_evenement.titre}")
                print(f"  - description: {db_evenement.description}")
                print(f"  - capacite_max: {db_evenement.capacite_max}")
                print(f"  - animateur: {db_evenement.animateur}")
                
                # Mise à jour des champs
                update_data = evenement.model_dump(exclude_unset=True)
                
                # Si les dates sont modifiées, mettre à jour le statut automatiquement
                if 'date_debut' in update_data or 'date_fin' in update_data:
                    new_date_debut = update_data.get('date_debut', db_evenement.date_debut)
                    new_date_fin = update_data.get('date_fin', db_evenement.date_fin)
                    new_statut = await self._determine_statut(new_date_debut, new_date_fin)
                    print(f"📊 Nouveau statut déterminé: {new_statut}")
                    update_data['statut'] = new_statut
                
                # Appliquer les mises à jour
                for field, value in update_data.items():
                    setattr(db_evenement, field, value)
                
                # Ajout explicite à la session
                db.add(db_evenement)
                print("➕ Événement ajouté à la session pour mise à jour")
                
                # Commit explicite
                print("\n🔄 Commit des modifications...")
                await db.flush()
                print("✅ Modifications flushées")
                
                # Rafraîchissement
                print("\n🔄 Rafraîchissement de l'événement...")
                await db.refresh(db_evenement)
                print(f"✅ Événement après mise à jour:")
                print(f"  - titre: {db_evenement.titre}")
                print(f"  - description: {db_evenement.description}")
                print(f"  - capacite_max: {db_evenement.capacite_max}")
                print(f"  - animateur: {db_evenement.animateur}")
                
                # Vérification des relations
                print("\n📊 Vérification des relations après mise à jour:")
                print(f"  - Nombre de besoins: {len(db_evenement.besoins)}")
                print(f"  - Nombre d'émargements: {len(db_evenement.emargements)}")
            
            print(f"\n🎉 MISE À JOUR RÉUSSIE POUR L'ÉVÉNEMENT {evenement_id}")
            print("=== FIN MISE À JOUR ÉVÉNEMENT ===\n")
            return db_evenement
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def delete_evenement(self, evenement_id: int) -> bool:
        """Supprime un événement"""
        print(f"\n=== 🗑️ DÉBUT SUPPRESSION ÉVÉNEMENT {evenement_id} ===")
        try:
            print(f"📌 État de la session avant suppression: {'active' if self.db.is_active else 'inactive'}")
            
            async with transaction_manager(self.db) as db:
                # Récupération de l'événement
                print(f"🔍 Recherche de l'événement {evenement_id}...")
                db_evenement = await self.get_evenement(evenement_id)
                print(f"✅ Événement trouvé: {db_evenement}")
                
                # Vérification des relations avant suppression
                print("\n📊 Relations à supprimer:")
                print(f"  - Nombre de besoins: {len(db_evenement.besoins)}")
                print(f"  - Nombre d'émargements: {len(db_evenement.emargements)}")
                
                # Suppression
                print("\n🗑️ Suppression de l'événement...")
                await db.delete(db_evenement)
                print("✅ Événement supprimé de la session")
            
            print(f"\n🎉 SUPPRESSION RÉUSSIE DE L'ÉVÉNEMENT {evenement_id}")
            print("=== FIN SUPPRESSION ÉVÉNEMENT ===\n")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def add_participant(self, evenement_id: int, inscription_id: int) -> Evenement:
        """Ajoute un participant à un événement"""
        db_evenement = await self.get_evenement(evenement_id)
        
        # Vérifier si l'événement est complet
        if db_evenement.est_complet:
            raise ValidationError("L'événement est complet")
        
        # Vérifier si le participant est déjà inscrit
        if any(ins.id == inscription_id for ins in db_evenement.inscriptions):
            raise ValidationError("Le participant est déjà inscrit à cet événement")
        
        # Ajouter le participant
        from app.models.models import Inscription
        result = await self.db.execute(
            select(Inscription).filter(Inscription.id == inscription_id)
        )
        inscription = result.scalar_one_or_none()
        if not inscription:
            raise NotFoundException(f"Inscription avec l'ID {inscription_id} non trouvée")
        
        db_evenement.inscriptions.append(inscription)
        await self.db.commit()
        await self.db.refresh(db_evenement)
        return db_evenement

    async def remove_participant(self, evenement_id: int, inscription_id: int) -> Evenement:
        """Retire un participant d'un événement"""
        db_evenement = await self.get_evenement(evenement_id)
        
        # Vérifier si le participant est inscrit
        inscription = next((ins for ins in db_evenement.inscriptions if ins.id == inscription_id), None)
        if not inscription:
            raise ValidationError("Le participant n'est pas inscrit à cet événement")
        
        db_evenement.inscriptions.remove(inscription)
        await self.db.commit()
        await self.db.refresh(db_evenement)
        return db_evenement

    async def get_participants(self, evenement_id: int) -> List[dict]:
        """Récupère la liste des participants d'un événement"""
        db_evenement = await self.get_evenement(evenement_id)
        return [
            {
                "id": ins.id,
                "nom": ins.nom,
                "prenom": ins.prenom,
                "email": ins.email,
                "telephone": ins.telephone,
                "date_inscription": ins.date_inscription
            }
            for ins in db_evenement.inscriptions
        ]

    async def update_statut(self, evenement_id: int, nouveau_statut: str) -> Evenement:
        """Met à jour le statut d'un événement (uniquement pour annule)"""
        print(f"\n=== 🔄 DÉBUT MISE À JOUR STATUT ÉVÉNEMENT {evenement_id} ===")
        try:
            db_evenement = await self.get_evenement(evenement_id)
            
            # Convertir en minuscules
            nouveau_statut = nouveau_statut.lower()
            
            # Vérifier si le statut est valide
            if nouveau_statut not in ["planifie", "en_cours", "termine", "annule"]:
                raise ValidationError("Statut invalide. Les statuts valides sont: planifie, en_cours, termine, annule")
            
            # Si on essaie de mettre un statut autre que annule, on recalcule automatiquement
            if nouveau_statut != "annule":
                nouveau_statut = await self._determine_statut(db_evenement.date_debut, db_evenement.date_fin)
                print(f"⚠️ Le statut a été recalculé automatiquement: {nouveau_statut}")
            
            async with transaction_manager(self.db) as db:
                print(f"📊 Mise à jour du statut: {db_evenement.statut} -> {nouveau_statut}")
                db_evenement.statut = nouveau_statut
                db.add(db_evenement)
            
            return db_evenement
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du statut: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_evenements_a_venir(self, limit: int = 10) -> List[Evenement]:
        """Récupère les événements à venir en se basant uniquement sur le statut"""
        print("\n=== 🎯 SERVICE: RÉCUPÉRATION ÉVÉNEMENTS À VENIR ===")
        try:
            # Utiliser l'enum StatutEvenement directement
            query = select(Evenement)\
                .filter(Evenement.statut == StatutEvenement.PLANIFIE)\
                .order_by(Evenement.date_debut)\
                .limit(limit)
            
            print("🔍 Requête SQL:")
            print("  - Statut = 'planifie'")
            print(f"  - Limite = {limit}")
            print("  - Tri par date de début")
            
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            print(f"\n✅ {len(events)} événements à venir trouvés")
            for event in events:
                print(f"  - {event.titre} (ID: {event.id})")
            
            print("=== FIN SERVICE ÉVÉNEMENTS À VENIR ===\n")
            return events
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def _diagnose_statuts(self):
        """Diagnostique les statuts actuels des événements"""
        print("\n=== 🔍 DIAGNOSTIC DES STATUTS ===")
        try:
            # Récupérer tous les événements avec leur statut
            query = select(Evenement).order_by(Evenement.id)
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            print(f"\n📊 État actuel des événements ({len(events)} trouvés):")
            if not events:
                print("  - Aucun événement dans la base de données")
            else:
                for event in events:
                    print(f"\n  Événement {event.id}:")
                    print(f"    - Titre: {event.titre}")
                    print(f"    - Statut actuel: {event.statut}")
                    print(f"    - Date début: {event.date_debut}")
                    print(f"    - Date fin: {event.date_fin}")
                    
                    # Calculer le statut attendu
                    expected_statut = await self._determine_statut(event.date_debut, event.date_fin, event.statut)
                    if expected_statut.upper() != event.statut:
                        print(f"    ⚠️ Statut incohérent:")
                        print(f"      - Statut actuel: {event.statut}")
                        print(f"      - Statut attendu: {expected_statut.upper()}")
            
            print("\n=== FIN DIAGNOSTIC DES STATUTS ===\n")
            
        except Exception as e:
            print(f"❌ Erreur lors du diagnostic: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_evenements_en_cours(self) -> List[Evenement]:
        """Récupère les événements en cours en se basant uniquement sur le statut"""
        print("\n=== 🎯 SERVICE: RÉCUPÉRATION ÉVÉNEMENTS EN COURS ===")
        try:
            # Diagnostic des statuts avant la requête
            await self._diagnose_statuts()
            
            # Utiliser l'enum StatutEvenement directement
            query = select(Evenement).filter(Evenement.statut == StatutEvenement.EN_COURS)
            
            print("🔍 Requête SQL:")
            print("  - Statut = 'en_cours'")
            
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            print(f"\n✅ {len(events)} événements en cours trouvés")
            for event in events:
                print(f"  - {event.titre} (ID: {event.id})")
            
            print("=== FIN SERVICE ÉVÉNEMENTS EN COURS ===\n")
            return events
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def get_evenements_termines(self, limit: int = 10) -> List[Evenement]:
        """Récupère les événements terminés en se basant uniquement sur le statut"""
        print("\n=== 🎯 SERVICE: RÉCUPÉRATION ÉVÉNEMENTS TERMINÉS ===")
        try:
            # Utiliser l'enum StatutEvenement directement
            query = select(Evenement)\
                .filter(Evenement.statut == StatutEvenement.TERMINE)\
                .order_by(Evenement.date_fin.desc())\
                .limit(limit)
            
            print("🔍 Requête SQL:")
            print("  - Statut = 'termine'")
            print(f"  - Limite = {limit}")
            print("  - Tri par date de fin (desc)")
            
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            print(f"\n✅ {len(events)} événements terminés trouvés")
            for event in events:
                print(f"  - {event.titre} (ID: {event.id})")
            
            print("=== FIN SERVICE ÉVÉNEMENTS TERMINÉS ===\n")
            return events
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise 

