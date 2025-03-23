from app.schemas.schema_rdv import CompteRenduRdvInput
from app.services.service_rdv import generer_resume, generer_conclusion
from app.services.service_generate_pdf_from_file import generate_pdf_from_html
from fastapi import APIRouter, Request
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, date
from app.utils import gr_code
import os
import base64
from app.config import get_base_url

router = APIRouter()

# Configurer un environnement Jinja pour génération hors navigateur
env = Environment(loader=FileSystemLoader("app/templates"))

def encode_image_to_base64(image_path):   
    with open(image_path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"

def render_template(template_name: str, **context):
    template = env.get_template(template_name)
    return template.render(**context)

@router.post("/generer-compte-rendu")
async def generer_compte_rendu(data: CompteRenduRdvInput, request: Request):
    # 🧠 Génération du résumé et de la conclusion automatiquement
    
    # 📄 Nom du fichier PDF final
    filename = f"compte_rendu_{data.nom_participant.replace(' ', '_')}.pdf"

    resume = await generer_resume(data.contenu_aborde)
    conclusion = await generer_conclusion(data.titre, data.objectif, resume)

    base_dir =  "file://" +os.path.abspath("app").replace("\\", "/")  # ← ✅ à utiliser ici

    logo_path = os.path.join("app", "static", "logo.png")
    logo_base64 = encode_image_to_base64(logo_path)

    base_url = get_base_url(request)
    file_url = f"{base_url.strip()}/fichiers/{filename}"

    qr_image = gr_code.generate_qr_base64(file_url)

    date_rdv_obj = datetime.strptime(data.date_rdv, "%Y-%m-%d")
    # 📝 Rendu HTML avec les données fusionnées
    rendered_html = render_template("compte_rendu_template.html",
    titre=data.titre,
    nom=data.nom_participant,
    lieu=data.lieu,
    date=date_rdv_obj.strftime("%d/%m/%Y"),
    objectif=data.objectif,
    resume=resume,
    conclusion=conclusion,
    coach=data.informations_coach,
    annee=date.today().year,
    base_url=base_dir,  # <-- C’est important pour le chemin absolu
    logo_base64=logo_base64,  # ✅ nouveau
    qr_code=qr_image
)   

    # 💾 Sauvegarder le HTML pour déboguer
    """debug_html_path = os.path.join("app", "temp_rendered_debug.html")
    with open(debug_html_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)"""

    # 🖨️ Génération du PDF avec ta fonction existante
    file_infos = await generate_pdf_from_html(rendered_html, filename, request)

    return {
        "message": "✅ Compte rendu généré avec succès.",
        "filename": file_infos.get("filename"),
        "file_url": file_infos.get("file_url"),
        "file_encoded": file_infos.get("file_encoded")
    }



