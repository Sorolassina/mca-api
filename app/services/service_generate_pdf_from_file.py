from weasyprint import HTML
from fastapi.responses import FileResponse
import io
from fastapi.responses import StreamingResponse
import uuid
from app.config import get_pdf_path

def generate_pdf_from_html(html_content: str, filename: str)-> str:

    """Génère un PDF et retourne le chemin du fichier."""
    try:
        pdf_path = get_pdf_path(filename)  # 📌 Utiliser le bon chemin
        HTML(string=html_content).write_pdf(pdf_path)
        return pdf_path  # ✅ Retourne juste le chemin du fichier
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du PDF : {str(e)}")  # ✅ Lève une erreur proprement
      
async def generate_pdf_from_file(html_content: str, filename:str)-> str:
    if not html_content.strip():
        raise ValueError("Le fichier HTML reçu est vide.")

    #pdf_filename = f"generated_{uuid.uuid4().hex}.pdf"
    pdf_path = get_pdf_path(filename)  # 📌 Sauvegarde propre
    
    try:
        HTML(string=html_content).write_pdf(pdf_path)
        return pdf_path  # ✅ Retourne le chemin du PDF généré
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du PDF : {str(e)}")
