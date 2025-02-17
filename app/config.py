  # Clé API Pappers (remplacez par la vôtre)
PAPPERS_API_KEY = "5c779e5cf0e04a3e814422345db7a29dc311bee60061ebd0"

import os

# 📌 Définir le chemin absolu du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 📁 Définir le dossier "fichiers/" pour stocker les PDFs
FICHIERS_DIR = os.path.join(BASE_DIR, "..", "fichiers")

# 📌 S'assurer que le dossier existe
os.makedirs(FICHIERS_DIR, exist_ok=True)

def get_pdf_path(filename: str) -> str:
    """ Retourne le chemin absolu d'un fichier PDF dans le dossier fichiers/ """
    return os.path.join(FICHIERS_DIR, filename)