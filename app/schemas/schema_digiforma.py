from pydantic import BaseModel,  Field, field_validator


class DigiformaInput(BaseModel):
    Password: str = Field(..., title="Entrer votre mot de passe pour accéder aux données")

    @field_validator("Password")
    @classmethod
    def validate_digi_content(cls, v):
        if v != "2311SLSs@1990":
            raise ValueError("Mot de passe incorrect.")
        return v