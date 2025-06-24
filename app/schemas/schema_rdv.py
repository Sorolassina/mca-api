from pydantic import BaseModel
from typing import List

class CompteRenduRdvInput(BaseModel):
    titre_rdv: str
    nom_participant: str
    prenom_participant: str
    evaluateur: str
    nom_coach: str
    prenom_coach: str
    activite: str
    attentes_generales: str
    date_rdv: str  # ou datetime si tu veux un format plus strict
    liste_observations: str  # String à traiter en splittant sur '-'
    liste_preconisations: str  # String à traiter en splittant sur '-'
    