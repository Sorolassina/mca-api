from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from app.models.models import TypeEvenement, StatutEvenement

class BesoinEvenementResponse(BaseModel):
    id: str
    titre: str
    description: Optional[str]
    date_evenement: datetime
    lieu: Optional[str]
    is_participant: bool
    nom: str
    prenom: str
    email: str

    class Config:
        from_attributes = True

class EmargementResponse(BaseModel):
    id: int
    signature_image: Optional[str]
    date_signature: datetime
    mode_signature: str
    is_validated: bool

    class Config:
        from_attributes = True

class EvenementBase(BaseModel):
    titre: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    date_debut: datetime
    date_fin: datetime
    lieu: Optional[str] = Field(None, max_length=255)
    type_evenement: TypeEvenement
    statut: StatutEvenement = Field(default=StatutEvenement.PLANIFIE)
    capacite_max: Optional[int] = Field(None, gt=0)
    animateur: Optional[str] = None
    id_prog: Optional[int] = Field(default=0)

    @validator('statut', pre=True)
    def convert_statut_to_lowercase(cls, v):
        """Convertit le statut en minuscules avant la validation"""
        if isinstance(v, str):
            return v.lower()
        return v

class EvenementCreate(EvenementBase):
    pass

class EvenementUpdate(EvenementBase):
    pass
    """titre: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    lieu: Optional[str] = Field(None, max_length=255)
    type_evenement: Optional[TypeEvenement] = None
    statut: Optional[StatutEvenement] = None
    capacite_max: Optional[int] = Field(None, gt=0)
    animateur: Optional[str] = None"""

class EvenementResponse(EvenementBase):
    id: int
    besoins: List[BesoinEvenementResponse] = []
    emargements: List[EmargementResponse] = []

    @property
    def nombre_participants(self) -> int:
        return len([b for b in self.besoins if b.is_participant])

    @property
    def est_complet(self) -> bool:
        if not hasattr(self, 'capacite_max') or self.capacite_max is None:
            return False
        return self.nombre_participants >= self.capacite_max

    @property
    def est_termine(self) -> bool:
        return datetime.utcnow() > self.date_fin

    @property
    def est_en_cours(self) -> bool:
        now = datetime.utcnow()
        return self.date_debut <= now <= self.date_fin

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EvenementInscription(BaseModel):
    inscription_id: int

class EvenementWithInscriptions(EvenementResponse):
    inscriptions: List[int]  # Liste des IDs des inscriptions 