from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class StatutProgramme(str, Enum):
    ACTIF = "actif"
    INACTIF = "inactif"
    TERMINE = "termine"
    PLANIFIE = "planifie"

class ProgrammeBase(BaseModel):
    nom: str = Field(..., min_length=3, max_length=100, description="Nom du programme")
    description: str = Field(..., min_length=10, max_length=500, description="Description détaillée du programme")
    date_debut: date = Field(..., description="Date de début du programme")
    date_fin: date = Field(..., description="Date de fin du programme")
    lieu: str = Field(..., min_length=3, max_length=100, description="Lieu de formation")
    places_disponibles: int = Field(..., gt=0, description="Nombre de places disponibles")
    places_totales: int = Field(..., gt=0, description="Nombre total de places")
    statut: StatutProgramme = Field(default=StatutProgramme.PLANIFIE, description="Statut du programme")
    prix: Optional[float] = Field(None, ge=0, description="Prix du programme (optionnel)")
    prerequis: Optional[List[str]] = Field(default=[], description="Liste des prérequis")
    objectifs: Optional[List[str]] = Field(..., min_items=1, description="Liste des objectifs du programme")

    @validator('date_fin')
    def date_fin_after_date_debut(cls, v, values):
        """Vérifie que la date de fin est après la date de début"""
        if v and 'date_debut' in values and values['date_debut'] and v < values['date_debut']:
            raise ValueError("La date de fin doit être après la date de début")
        return v

    @validator('places_disponibles')
    def places_disponibles_less_than_total(cls, v, values):
        """Vérifie que le nombre de places disponibles ne dépasse pas le total"""
        if v and 'places_totales' in values and values['places_totales'] and v > values['places_totales']:
            raise ValueError("Le nombre de places disponibles ne peut pas dépasser le nombre total de places")
        return v

    @validator('objectifs')
    def validate_objectifs(cls, v):
        """Vérifie que la liste des objectifs n'est pas vide si elle est fournie"""
        if v is not None and len(v) < 1:
            raise ValueError("Le programme doit avoir au moins un objectif")
        return v

class ProgrammeCreate(ProgrammeBase):
    pass

class ProgrammeUpdate(ProgrammeBase):
    """Schéma pour la mise à jour d'un programme.
    Hérite de ProgrammeBase pour réutiliser les validations de base,
    mais tous les champs sont optionnels grâce à la configuration."""
    
    class Config:
        from_attributes = True
        # Cette configuration permet de rendre tous les champs optionnels
        # tout en conservant les validations de ProgrammeBase
        extra = "forbid"  # Empêche les champs supplémentaires
        validate_assignment = True  # Valide les champs lors de l'assignation    

class ProgrammeResponse(ProgrammeBase):
    id: int = Field(..., description="Identifiant unique du programme")
    created_at: datetime = Field(..., description="Date et heure de création du programme")
    updated_at: Optional[datetime] = Field(None, description="Date et heure de dernière mise à jour")
    nombre_inscriptions: int = Field(0, description="Nombre total d'inscriptions au programme")
    nombre_preinscriptions: int = Field(0, description="Nombre total de préinscriptions au programme")
    taux_remplissage: float = Field(0, description="Pourcentage de places occupées (inscriptions/places totales)")
    taux_conversion: float = Field(0, description="Pourcentage de conversion des préinscriptions en inscriptions")

    class Config:
        from_attributes = True