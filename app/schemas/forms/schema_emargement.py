from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class EmargementBase(BaseModel):
    email: str
    evenement_id: int
    mode_signature: str
    signature_image: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class EmargementCreate(BaseModel):
    evenement_id: int
    mode_signature: str
    email: str

class EmargementCreateResponse(BaseModel):
    emargement: dict
    signature_url: Optional[str] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True

class EmargementUpdate(BaseModel):
    mode_signature: Optional[str] = None
    signature_image: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_validated: Optional[bool] = None

class EmargementResponse(EmargementBase):
    id: int
    date_signature: datetime
    is_validated: bool
    photo_profil: Optional[str] = None

    class Config:
        from_attributes = True

class EmargementSignature(BaseModel):
    signature_image: str
    photo_profil: Optional[str] = None
    token: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class EmargementValidation(BaseModel):
    is_validated: bool

class EmargementListResponse(BaseModel):
    emargements: List[EmargementResponse]
    total: int
    validated: int
    pending: int 