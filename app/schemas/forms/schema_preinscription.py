# app/schemas/forms/schema_preinscription.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum
import re

class SituationProfessionnelle(str, Enum):
    DEMANDEUR_EMPLOI = "demandeur_emploi"
    SALARIE = "salarie"
    INDEPENDANT = "independant"
    ETUDIANT = "etudiant"
    AUTRE = "autre"

class NiveauEtude(str, Enum):
    SANS_DIPLOME = "sans_diplome"
    CAP_BEP = "cap_bep"
    BAC = "bac"
    BAC_PLUS_2 = "bac_plus_2"
    BAC_PLUS_3 = "bac_plus_3"
    BAC_PLUS_4 = "bac_plus_4"
    BAC_PLUS_5 = "bac_plus_5"
    SUPERIEUR = "superieur"

class PreinscriptionForm(BaseModel):
    # Identifiants de liaison
    programme_id: int = Field(..., title="ID du programme de formation", gt=0)
    event_id: Optional[int] = Field(None, title="ID de l'événement")
    
    # Informations personnelles
    nom: str = Field(..., min_length=2, max_length=50, title="Nom")
    prenom: str = Field(..., min_length=2, max_length=50, title="Prénom")
    email: EmailStr = Field(..., title="Email")
    telephone: str = Field(..., title="Téléphone")
    date_naissance: date = Field(..., title="Date de naissance")
    adresse: str = Field(..., min_length=5, max_length=200, title="Adresse")
    code_postal: str = Field(..., title="Code postal")
    ville: str = Field(..., min_length=2, max_length=100, title="Ville")
    
    # Informations professionnelles
    situation_professionnelle: SituationProfessionnelle = Field(
        ..., 
        title="Situation professionnelle"
    )
    niveau_etude: NiveauEtude = Field(..., title="Niveau d'études")
    projet_entrepreneurial: Optional[str] = Field(
        None, 
        max_length=500,
        title="Projet entrepreneurial",
        description="Description de votre projet (maximum 500 caractères)"
    )
    
    # Consentement RGPD
    rgpd_consent: bool = Field(
        ...,
        title="Consentement RGPD",
        description="Acceptation de la politique de protection des données personnelles"
    )
    
    # Métadonnées
    date_soumission: date = Field(default_factory=date.today, title="Date de soumission")
    source: str = Field(default="formulaire_web", title="Source de la préinscription")

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: Optional[int]) -> Optional[int]:
        """Valide que event_id est soit None, soit un entier positif"""
        if v is not None and v <= 0:
            raise ValueError("L'ID de l'événement doit être un entier positif")
        return v

    @field_validator("telephone")
    @classmethod
    def validate_telephone(cls, v: str) -> str:
        """Valide le format du numéro de téléphone français"""
        if not re.match(r'^(\+33|0)[1-9](\d{2}){4}$', v):
            raise ValueError("Le numéro de téléphone doit être au format français (+33612345678 ou 0612345678)")
        return v

    @field_validator("code_postal")
    @classmethod
    def validate_code_postal(cls, v: str) -> str:
        """Valide le format du code postal français"""
        if not re.match(r'^\d{5}$', v):
            raise ValueError("Le code postal doit contenir 5 chiffres")
        return v

    @field_validator("date_naissance")
    @classmethod
    def validate_date_naissance(cls, v: date) -> date:
        """Vérifie que la date de naissance est valide (personne majeure)"""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Vous devez être majeur pour vous préinscrire")
        return v

    @field_validator("rgpd_consent")
    @classmethod
    def validate_rgpd_consent(cls, v: bool) -> bool:
        """Vérifie que le consentement RGPD a été donné"""
        if not v:
            raise ValueError("Vous devez accepter la politique de protection des données personnelles pour continuer")
        return v