import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import Request

print("✅ [DEBUG] Fichier config.py chargé !")

# Chemins des dossiers statiques
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
FICHIERS_DIR = BASE_DIR / "fichiers"
STATIC_IMAGES_DIR = STATIC_DIR / "images"
STATIC_MAPS_DIR = STATIC_DIR / "maps"

# Création des dossiers s'ils n'existent pas
for directory in [STATIC_DIR, TEMPLATE_DIR, FICHIERS_DIR, STATIC_IMAGES_DIR, STATIC_MAPS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    # Configuration de la base de données
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: str
    
    # Construction de l'URL de la base de données
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Configuration de l'API
    API_BASE_URL: str = "https://api.mycreo.com"
    
    # Configuration JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuration de l'application
    APP_NAME: str = "MCA API"
    DEBUG: bool = False
    
    # Configuration des fichiers uploadés
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max-limit
    
    # Configuration des emails
    SMTP_TLS: bool = True
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_SENDER: str
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_RECIPIENT: Optional[str] = None

    # Clés API (optionnelles)
    PAPPERS_API_KEY: Optional[str] = None
    DIGIFORMA_API_KEY: Optional[str] = None
    DIGIFORMAT_PASSWORD: Optional[str] = None

    # URL du site MCA
    MCA_WEBSITE_URL: str = "https://lesentrepreneursaffranchis.fr/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Permet les champs supplémentaires non définis
    )

# Instance des paramètres
settings = Settings()

# Créer le dossier uploads s'il n'existe pas
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

def get_pdf_path(filename: str) -> str:
    """ Retourne le chemin absolu d'un fichier PDF dans le dossier fichiers/ """
    return os.path.join(FICHIERS_DIR, filename)

def get_base_url(request: Request):
    """Détecte dynamiquement l'URL de l'API"""
    base_url = str(request.base_url).rstrip("/")
    return base_url



