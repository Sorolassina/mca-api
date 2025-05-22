from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date

class NiveauConnaissance(str):
    DEBUTANT = "debutant"
    INTERMEDIAIRE = "intermediaire"
    AVANCE = "avance"

class BesoinForm(BaseModel):
    # Infos participant
    nom: str = Field(..., min_length=2, max_length=50, title="Nom")
    prenom: str = Field(..., min_length=2, max_length=50, title="Prénom")
    email: EmailStr = Field(..., title="Email")
    
    # Infos besoins
    besoins_principaux: str = Field(..., min_length=10, max_length=1000, title="Besoins principaux")
    attentes: Optional[str] = Field(None, max_length=1000, title="Attentes vis-à-vis de l'événement")
    niveau_connaissance: str = Field(..., title="Niveau de connaissance du sujet")
    objectifs: Optional[str] = Field(None, max_length=1000, title="Objectifs personnels")
    contraintes: Optional[str] = Field(None, max_length=1000, title="Contraintes ou questions particulières")
    is_participant: bool = Field(..., title="Confirmation de participation")
    
    # Consentement RGPD
    rgpd_consent: bool = Field(..., title="Consentement RGPD")
    rgpd_consent_date: Optional[date] = Field(None, title="Date du consentement RGPD")

    @field_validator("rgpd_consent")
    @classmethod
    def validate_rgpd_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Vous devez accepter la politique de protection des données personnelles pour continuer")
        return v 