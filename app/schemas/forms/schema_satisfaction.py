from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date

class SatisfactionForm(BaseModel):
    # Infos participant
    nom: Optional[str] = Field(None, min_length=2, max_length=50, title="Nom")
    prenom: Optional[str] = Field(None, min_length=2, max_length=50, title="Prénom")
    email: EmailStr = Field(..., title="Email")

    # Satisfaction
    note_globale: int = Field(..., ge=1, le=5, title="Note globale (1 à 5)")
    points_positifs: Optional[str] = Field(None, max_length=1000, title="Points positifs")
    points_amelioration: Optional[str] = Field(None, max_length=1000, title="Points à améliorer")
    recommander: bool = Field(..., title="Recommanderiez-vous l'événement ?")
    commentaires: Optional[str] = Field(None, max_length=1000, title="Commentaires libres")
    opinion_evaluateur: Optional[str] = Field(None, max_length=1000, title="Votre opinion sur l'évaluateur")

    # Consentement RGPD
    rgpd_consent: bool = Field(..., title="Consentement RGPD")
    rgpd_consent_date: Optional[date] = Field(None, title="Date du consentement RGPD")

    @field_validator("rgpd_consent")
    @classmethod
    def validate_rgpd_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Vous devez accepter la politique de protection des données personnelles pour continuer")
        return v 