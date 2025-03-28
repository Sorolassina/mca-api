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
from pathlib import Path
from app.config import STATIC_DIR

router = APIRouter()

# Configurer un environnement Jinja pour génération hors navigateur
env = Environment(loader=FileSystemLoader("app/templates"))

"""def encode_image_to_base64(image_path):   
    with open(image_path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"""
    
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return f"data:image/svg+xml;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"

def render_template(template_name: str, **context):
    template = env.get_template(template_name)
    return template.render(**context)

@router.post("/generer-compte-rendu")
async def generer_compte_rendu(data: CompteRenduRdvInput, request: Request):
    # 🧠 Génération du résumé et de la conclusion automatiquement
    
    # 📄 Nom du fichier PDF final
    filename = f"compte_rendu_{data.nom_participant.replace(' ', '_')}.pdf"

    #resume = await generer_resume(data.contenu_aborde)
    #conclusion = await generer_conclusion(data.titre, data.objectif, resume)

    base_dir =  Path("app").resolve().as_uri() #"file://" +os.path.abspath("app").replace("\\", "/")  # ← ✅ à utiliser ici

    logo_path = os.path.join(STATIC_DIR, "Banniere.svg")
    logo_base64 = encode_image_to_base64(logo_path)

    base_url = get_base_url(request)
    file_url = f"{base_url.strip()}/fichiers/{filename}"

    qr_image = gr_code.generate_qr_base64(file_url)

    date_rdv_obj = datetime.strptime(data.date_rdv, "%d/%m/%Y")
    # 📝 Rendu HTML avec les données fusionnées
    rendered_html = render_template("compte_rendu_new.html",
    titre_rdv=data.titre_rdv,
    nom_participant=data.nom_participant,
    prenom_participant=data.prenom_participant,
    nom_coach=data.nom_coach,
    prenom_coach=data.prenom_coach,
    evaluateur=data.evaluateur,
    date_rdv=date_rdv_obj.strftime("%d/%m/%Y"),
    activite=data.activite,
    attentes_generales=data.attentes_generales,
    liste_observations=data.liste_observations,
    liste_preconisations=data.liste_preconisations,
    annee=date.today().year,
    base_url=base_dir,  # <-- C’est important pour le chemin absolu
    logo_base64=logo_base64,  # ✅ nouveau
    qr_code=qr_image
)   

    # 🖨️ Génération du PDF avec ta fonction existante
    file_infos = await generate_pdf_from_html(rendered_html, filename, request)

    return {
        "message": "✅ Compte rendu généré avec succès.",
        "filename": file_infos.get("filename"),
        "file_url": file_infos.get("file_url"),
        "file_encoded": f"data:application/pdf;base64,{file_infos.get("file_encoded")}"
    }



