from pydantic import BaseModel,  Field, field_validator
from app.config import settings

class DigiformaInput(BaseModel):
    Password: str = Field(..., title="Entrer votre mot de passe pour accéder aux données")

    @field_validator("Password")
    @classmethod
    def validate_digi_content(cls, v):
        if v != settings.DIGIFORMAT_PASSWORD:
            raise ValueError("Mot de passe incorrect.")
        return v