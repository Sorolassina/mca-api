from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.service_generate_pdf_from_file import generate_pdf_from_html, generate_pdf_from_file
from app.models.model_Html import HTMLInput, HTMLFileInput
from fastapi.responses import FileResponse
import mimetypes

router = APIRouter()

@router.post("/generate-pdf", response_class=FileResponse)
def generate_pdf(data: HTMLInput):
    if not data.html_content:
        raise HTTPException(status_code=400, detail="Le contenu HTML est vide.")
    
    file_path = generate_pdf_from_html(data.html_content)  # ✅ Retourne un chemin

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="generated.pdf",
        headers={"Content-Disposition": "attachment; filename=generated.pdf"}
    )  # ✅ Retourne correctement le fichier PDF


@router.post("/generate-pdf-from-file", response_class=FileResponse)
async def generate_pdf_from_html_file(file: UploadFile = File(...)):
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

    file_path = await generate_pdf_from_file(validated_data.content)  # ✅ Retourne un chemin
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="uploaded_generated.pdf",
        headers={"Content-Disposition": "attachment; filename=uploaded_generated.pdf"}
    )  # ✅ Retourne correctement le fichier