
import os
from dotenv import load_dotenv
from fastapi import Request
# Charger le fichier .env
load_dotenv()

print("✅ [DEBUG] Fichier config.py chargé !")

# 📌 Définir le chemin absolu du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 📁 Définir le dossier "fichiers/" pour stocker les PDFs
FICHIERS_DIR = os.path.join(BASE_DIR, "static", "fichiers")
# 📌 S'assurer que le dossier existe
os.makedirs(FICHIERS_DIR, exist_ok=True)
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Dossiers pour stocker les cartes et images
STATIC_MAPS_DIR = os.path.join(BASE_DIR, "static", "maps") 
STATIC_IMAGES_DIR = os.path.join(BASE_DIR, "static", "images") 
# Créer les dossiers s'ils n'existent pas
os.makedirs(STATIC_MAPS_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates") 
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# Clés API  
PAPPERS_API_KEY = os.getenv("PAPPERS_API_KEY")
DIGIFORMA_API_KEY  = os.getenv("DIGIFORMA_API_KEY")

# ✅ Paramètres SMTP pour l'envoi des emails
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "sorolassina58@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # 🔥 Ne PAS mettre le mot de passe en dur !
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "lassina.soro.edu@groupe-gema.com")

def get_pdf_path(filename: str) -> str:
    """ Retourne le chemin absolu d'un fichier PDF dans le dossier fichiers/ """
    return os.path.join(FICHIERS_DIR, filename)

def get_base_url(request: Request):
    """Détecte dynamiquement l'URL de l'API"""
    base_url = str(request.base_url).rstrip("/")
    return base_url



