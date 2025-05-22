# app/models/models.py
from sqlalchemy import Column, String, Integer, Float, DateTime,Date, Enum, ForeignKey, Table, Text, func, Boolean
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from datetime import date
import enum
import re
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

#-------------------------------------PROGRAMME-------------------------------------
# Enums
class StatutProgramme(str, enum.Enum):
    ACTIF = "actif"
    INACTIF = "inactif"
    TERMINE = "termine"
    PLANIFIE = "planifie"

class SituationProfessionnelle(str, enum.Enum):
    DEMANDEUR_EMPLOI = "demandeur_emploi"
    SALARIE = "salarie"
    INDEPENDANT = "independant"
    ETUDIANT = "etudiant"
    AUTRE = "autre"

class NiveauEtude(str, enum.Enum):
    SANS_DIPLOME = "sans_diplome"
    CAP_BEP = "cap_bep"
    BAC = "bac"
    BAC_PLUS_2 = "bac_plus_2"
    BAC_PLUS_3 = "bac_plus_3"
    BAC_PLUS_4 = "bac_plus_4"
    BAC_PLUS_5 = "bac_plus_5"
    SUPERIEUR = "superieur"

# Modèle Programme
class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    lieu = Column(String(100), nullable=False)
    places_disponibles = Column(Integer, nullable=False)
    places_totales = Column(Integer, nullable=False)
    statut = Column(Enum(StatutProgramme), nullable=False, default=StatutProgramme.PLANIFIE)
    prix = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    # Relations
    prerequis = relationship("ProgrammePrerequis", back_populates="programme")
    objectifs = relationship("ProgrammeObjectif", back_populates="programme", order_by="ProgrammeObjectif.ordre")
    preinscriptions = relationship("Preinscription", back_populates="programme")

    def __repr__(self):
        return f"<Programme(id='{self.id}', nom='{self.nom}', statut='{self.statut}')>"


# Tables d'association (définies après les modèles)
class ProgrammePrerequis(Base):
    __tablename__ = 'programme_prerequis'
    
    id = Column(Integer, primary_key=True, autoincrement=True, server_default=func.nextval('programme_prerequis_id_seq'))
    programme_id = Column(Integer, ForeignKey('programmes.id'), nullable=False)
    prerequis = Column(String, nullable=False)
    
    programme = relationship("Programme", back_populates="prerequis")

    def __repr__(self):
        return f"<ProgrammePrerequis(id={self.id}, programme_id={self.programme_id})>"

class ProgrammeObjectif(Base):
    __tablename__ = 'programme_objectifs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, server_default=func.nextval('programme_objectifs_id_seq'))
    programme_id = Column(Integer, ForeignKey('programmes.id'), nullable=False)
    objectif = Column(String, nullable=False)
    ordre = Column(Integer, nullable=False)
    
    programme = relationship("Programme", back_populates="objectifs")

    def __repr__(self):
        return f"<ProgrammeObjectif(id={self.id}, programme_id={self.programme_id}, ordre={self.ordre})>"

#-------------------------------------PREINSCRIPTION-------------------------------------
# Modèle Preinscription
class Preinscription(Base):
    __tablename__ = "preinscriptions"

    # Identifiants de liaison
    id = Column(Integer, primary_key=True, autoincrement=True)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("evenements.id"), nullable=True)
    
    # Informations personnelles
    nom = Column(String(50), nullable=False)
    prenom = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=False)
    date_naissance = Column(Date, nullable=False)
    adresse = Column(String(200), nullable=False)
    code_postal = Column(String(5), nullable=False)
    ville = Column(String(100), nullable=False)
    
    # Informations professionnelles
    situation_professionnelle = Column(Enum(SituationProfessionnelle), nullable=False)
    niveau_etude = Column(Enum(NiveauEtude), nullable=False)
    projet_entrepreneurial = Column(Text, nullable=True)
    
    # Consentement RGPD
    rgpd_consent = Column(Boolean, nullable=False, default=False)
    rgpd_consent_date = Column(Date, nullable=False, server_default=func.CURRENT_DATE())
    
    # Métadonnées
    date_soumission = Column(Date, nullable=False, server_default=func.CURRENT_DATE())
    source = Column(String(50), nullable=False, default="formulaire_web")

    # Relations
    programme = relationship("Programme", back_populates="preinscriptions")

    def __repr__(self):
        return f"<Preinscription(id='{self.id}', nom='{self.nom}', prenom='{self.prenom}')>"

    @validates('telephone')
    def validate_telephone(self, key, value):
        """Valide le format du numéro de téléphone français"""
        if not re.match(r'^(\+33|0)[1-9](\d{2}){4}$', value):
            raise ValueError("Le numéro de téléphone doit être au format français (+33612345678 ou 0612345678)")
        return value

    @validates('code_postal')
    def validate_code_postal(self, key, value):
        """Valide le format du code postal français"""
        if not re.match(r'^\d{5}$', value):
            raise ValueError("Le code postal doit contenir 5 chiffres")
        return value

    @validates('date_naissance')
    def validate_date_naissance(self, key, value):
        """Vérifie que la date de naissance est valide (personne majeure)"""
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Vous devez être majeur pour vous préinscrire")
        return value

#-------------------------------------INSCRIPTION-------------------------------------
class Inscription(Base):
    __tablename__ = "inscriptions"

    # Identifiants de liaison
    id = Column(Integer, primary_key=True, autoincrement=True)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    preinscription_id = Column(Integer, ForeignKey("preinscriptions.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("evenements.id"), nullable=True)

    # Informations personnelles
    nom = Column(String(50), nullable=False)
    prenom = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=False)
    date_naissance = Column(Date, nullable=False)
    adresse = Column(String(200), nullable=False)
    code_postal = Column(String(5), nullable=False)
    ville = Column(String(100), nullable=False)

    # Informations professionnelles
    situation_professionnelle = Column(Enum(SituationProfessionnelle, name="situationprofessionnelle_insc"), nullable=False)
    niveau_etude = Column(Enum(NiveauEtude, name="niveauetude_insc"), nullable=False)
    projet_entrepreneurial = Column(Text, nullable=True)

    # Consentement RGPD
    rgpd_consent = Column(Boolean, nullable=False, default=False)
    rgpd_consent_date = Column(Date, nullable=False, server_default=func.CURRENT_DATE())

    # Métadonnées
    date_inscription = Column(Date, nullable=False, server_default=func.CURRENT_DATE())
    source = Column(String(50), nullable=False, default="formulaire_web")

    # Relations
    programme = relationship("Programme")
    preinscription = relationship("Preinscription")

    def __repr__(self):
        return f"<Inscription(id='{self.id}', nom='{self.nom}', prenom='{self.prenom}')>"


#-------------------------------------BESOINS EVENEMENT-------------------------------------
class BesoinEvenement(Base):
    __tablename__ = "besoins_evenement"

    id = Column(String(50), primary_key=True)  # Changé en String pour le format "besoin_X_UUID"
    event_id = Column(Integer, ForeignKey("evenements.id", ondelete="CASCADE"), nullable=False)
    titre = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    date_evenement = Column(Date, nullable=False)
    nb_jours = Column(Integer, nullable=True)
    lieu = Column(String(100), nullable=True)
    is_participant = Column(Boolean, nullable=True, default=False)
    
    # Infos participant
    nom = Column(String(50), nullable=False)
    prenom = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)

    # Infos besoins
    besoins_principaux = Column(Text, nullable=False)
    attentes = Column(Text, nullable=True)
    niveau_connaissance = Column(String(20), nullable=False)
    objectifs = Column(Text, nullable=True)
    contraintes = Column(Text, nullable=True)

    # Consentement RGPD
    rgpd_consent = Column(Boolean, nullable=False, default=False)
    rgpd_consent_date = Column(Date, nullable=True)

    date_soumission = Column(Date, nullable=False, server_default=func.CURRENT_DATE())

    # Relations
    evenement = relationship("Evenement", back_populates="besoins")

    def __repr__(self):
        return f"<BesoinEvenement(id='{self.id}', event_id='{self.event_id}', email='{self.email}')>"


#-------------------------------------SATISFACTION EVENEMENT-------------------------------------
class SatisfactionEvenement(Base):
    __tablename__ = "satisfaction_evenement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("evenements.id"), nullable=False)
    email = Column(String(100), nullable=False)
    nom = Column(String(50), nullable=True)
    prenom = Column(String(50), nullable=True)
    note_globale = Column(Integer, nullable=False)
    points_positifs = Column(Text, nullable=True)
    points_amelioration = Column(Text, nullable=True)
    recommander = Column(Boolean, nullable=False)
    commentaires = Column(Text, nullable=True)
    opinion_evaluateur = Column(Text, nullable=True)
    rgpd_consent = Column(Boolean, nullable=False, default=False)
    rgpd_consent_date = Column(Date, nullable=True)
    date_soumission = Column(Date, nullable=False, server_default=func.CURRENT_DATE())

    def __repr__(self):
        return f"<SatisfactionEvenement(id='{self.id}', event_id='{self.event_id}', email='{self.email}')>"
    

#-------------------------------------EMARGEMENT-------------------------------------
class Emargement(Base):
    __tablename__ = "emargements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evenement_id = Column(Integer, ForeignKey("evenements.id", ondelete="CASCADE"), nullable=False)
    signature_image = Column(String, nullable=False, server_default="")  # Permet une chaîne vide par défaut
    photo_profil = Column(String, nullable=True)  # Nouvelle colonne pour la photo du signataire
    date_signature = Column(DateTime, default=datetime.utcnow)
    mode_signature = Column(String, nullable=False)  # 'distant' ou 'presentiel'
    ip_address = Column(String, nullable=True)  # Pour le mode distant
    user_agent = Column(String, nullable=True)  # Pour le mode distant
    is_validated = Column(Boolean, default=False)  # Pour le mode présentiel
    email = Column(String(100), nullable=False)
    # Relations
    evenement = relationship("Evenement", back_populates="emargements")

    def __repr__(self):
        return f"<Emargement {self.id} - Evenement: {self.evenement_id}>" 
    
#-------------------------------------EVENEMENT-------------------------------------

class TypeEvenement(str, PyEnum):
    FORMATION = "formation"
    ATELIER = "atelier"
    CONFERENCE = "conference"
    SEMINAIRE = "seminaire"
    TABLE_RONDE = "table_ronde"
    WORKSHOP = "workshop"
    AUTRE = "autre"

class StatutEvenement(str, PyEnum):
    PLANIFIE = "planifie"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ANNULE = "annule"

class Evenement(Base):
    __tablename__ = "evenements"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    titre = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date_debut = Column(DateTime(timezone=True), nullable=False)
    date_fin = Column(DateTime(timezone=True), nullable=False)
    lieu = Column(String(255), nullable=True)
    type_evenement = Column(Enum(TypeEvenement), nullable=False)
    statut = Column(Enum(StatutEvenement), nullable=False, default=StatutEvenement.PLANIFIE)
    capacite_max = Column(Integer, nullable=True)
    animateur = Column(Text, nullable=True) # L'animateur est aussi une inscription
    id_prog = Column(Integer, ForeignKey("programmes.id"), nullable=True, default=0)  # Nouvelle colonne

    # Relations
    programme = relationship("Programme", backref="evenements")  # Nouvelle relation
    besoins = relationship("BesoinEvenement", 
                         back_populates="evenement",
                         cascade="all, delete-orphan",
                         lazy="selectin")
    
    emargements = relationship("Emargement", 
                            back_populates="evenement",
                            cascade="all, delete-orphan",
                            lazy="selectin")

    def __repr__(self):
        return f"<Evenement {self.id} - {self.titre} - {self.date_debut.strftime('%d/%m/%Y')}>"

    @property
    def nombre_participants(self):
        """Retourne le nombre de participants inscrits."""
        return len([b for b in self.besoins if b.is_participant])

    @property
    def est_complet(self):
        """Vérifie si l'événement a atteint sa capacité maximale."""
        if self.capacite_max is None:
            return False
        return self.nombre_participants >= self.capacite_max

    @property
    def est_termine(self):
        """Vérifie si l'événement est terminé."""
        return datetime.utcnow() > self.date_fin

    @property
    def est_en_cours(self):
        """Vérifie si l'événement est en cours."""
        now = datetime.utcnow()
        return self.date_debut <= now <= self.date_fin 

