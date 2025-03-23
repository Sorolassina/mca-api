from pydantic import BaseModel
from typing import List

class CompteRenduRdvInput(BaseModel):
    titre: str
    nom_participant: str
    lieu: str
    date_rdv: str  # ou datetime si tu veux un format plus strict
    objectif: str
    contenu_aborde: List[str]  # Liste d’éléments à résumer
    informations_coach: str