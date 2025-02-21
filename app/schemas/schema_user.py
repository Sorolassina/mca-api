from pydantic import BaseModel, EmailStr, Field

class UserInDB(BaseModel):
    username: str = Field(..., description="Nom d'utilisateur unique")
    name: str = Field(..., description="Nom de famille")
    firstname: str = Field(..., description="Prénom")
    email: EmailStr = Field(..., description="Adresse email sur laquelle vous sera envoyé votre clé")
    password: str = Field(..., min_length=6, description="Mot de passe sécurisé (6 caractères minimum)")

    class Config:
        orm_mode = True  # ✅ Permet d'utiliser le modèle avec SQLAlchemy
