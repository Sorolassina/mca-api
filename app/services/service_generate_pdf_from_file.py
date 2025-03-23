from weasyprint import HTML
from app.config import get_pdf_path
from app.utils.file_encoded import encode_file_to_base64
from app.config import get_base_url
from fastapi import Request
import os

async def generate_pdf_from_html(html_content: str, filename: str, request:Request)-> str:
    base_url = get_base_url(request)  # Récupérer l'URL dynamique
    """Génère un PDF et retourne le chemin du fichier."""
    try:
        pdf_path = get_pdf_path(filename)  # 📌 Utiliser le bon chemin
        #base_dir = os.path.abspath("app") 
        HTML(string=html_content).write_pdf(pdf_path)

        # Construction de l'URL de base
        file_url = f"/fichiers/{filename}"

        # Vérifie si l’image existe avant d’essayer de l’encoder
        if os.path.exists(pdf_path):
            encoded_file = encode_file_to_base64(pdf_path)
        else:
            encoded_file = None  # Si l’image n’existe pas

        return {
                "filename": filename,
                "file_url":f"{base_url.strip()}{file_url.strip()}",
                "file_encoded" : encoded_file
                }  # ✅ Retourne un dictionnaire


    except Exception as e:
        raise Exception(f"Erreur lors de la génération du PDF : {str(e)}")  # ✅ Lève une erreur proprement
      
"""async def generate_pdf_from_file(html_content: str, filename:str, request:Request)-> str:
    base_url = get_base_url(request)  # Récupérer l'URL dynamique
    if not html_content.strip():
        raise ValueError("Le fichier HTML reçu est vide.")

    pdf_path = get_pdf_path(filename)  # 📌 Sauvegarde propre
    
    try:
        HTML(string=html_content).write_pdf(pdf_path)

        # Construction de l'URL de base
        file_url = f"/fichiers/{filename}"
       
        # Vérifie si l’image existe avant d’essayer de l’encoder
        if os.path.exists(pdf_path):
            encoded_file = encode_file_to_base64(pdf_path)
        else:
            encoded_file = None  # Si le fichier n’existe pas

        return {
                "filename": filename,
                "file_url":f"{base_url.strip()}{file_url.strip()}",
                "file_encoded" : encoded_file
                }  # ✅ Retourne un dictionnaire
    
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du PDF : {str(e)}")
"""