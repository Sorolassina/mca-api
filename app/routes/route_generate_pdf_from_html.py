from fastapi import APIRouter, UploadFile, HTTPException
from app.services.service_generate_pdf_from_file import generate_pdf_from_html
from app.schemas.schema_Html import HTMLInput, HTMLFileInput
import os

from fastapi import Request

router = APIRouter()


@router.post("/generate-pdf")
async def generate_pdf(data: HTMLInput, request:Request)-> dict:
    
    filename = data.filename 
    # Vérifier et forcer l'extension .pdf
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    if not data.html_content:
        raise HTTPException(status_code=400, detail="Le contenu HTML est vide.")
    
    file_infos= await generate_pdf_from_html(data.html_content,filename, request)  # ✅ Retourne un chemin

    return file_infos


@router.post("/generate-pdf-from-file")
async def generate_pdf_from_html_file(file: UploadFile, request:Request)-> dict:

    # 🔹 Récupérer le nom de fichier sans son extension et ajouter `.pdf`
    base_filename = os.path.splitext(file.filename)[0]  # Extrait le nom sans l'extension
    filename = f"{base_filename}.pdf"  # Remplace l'extension

    # Lire le contenu du fichier
    file_content = await file.read()
    
    # Vérifier que le contenu est bien du HTML en utilisant notre modèle Pydantic
    decoded_content = file_content.decode("utf-8", errors="ignore")
    if not decoded_content.strip():
        raise HTTPException(status_code=400, detail="Le fichier HTML est vide après décodage.")
    try:
        
        validated_data = HTMLFileInput(
            filename=file.filename, 
            content=decoded_content
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_infos = await generate_pdf_from_html(validated_data.content,filename,request)  # ✅ Retourne un chemin
    
    return file_infos  # ✅ Retourne correctement les informations

