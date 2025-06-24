from app.schemas.schema_rdv import CompteRenduRdvInput
from app.services.service_rdv import generer_resume, generer_conclusion
from app.services.service_generate_pdf_from_file import generate_pdf_from_html
from fastapi import APIRouter, Request, HTTPException
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, date
from app.utils import gr_code
from app.utils.date_convertUTC import ensure_utc, parse_date_string
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
    print("🚀 Début de la génération du compte rendu...")
    try:
        # 🧠 Génération du résumé et de la conclusion automatiquement
        print("📝 Préparation des données...")
        
        # 📄 Nom du fichier PDF final
        filename = f"compte_rendu_{data.nom_participant.replace(' ', '_')}.pdf"
        print(f"📄 Nom du fichier généré : {filename}")

        #resume = await generer_resume(data.contenu_aborde)
        #conclusion = await generer_conclusion(data.titre, data.objectif, resume)

        print("🔍 Configuration des chemins...")
        base_dir = Path("app").resolve().as_uri()
        print(f"📂 Répertoire de base : {base_dir}")

        logo_path = os.path.join(STATIC_DIR, "Banniere.svg")
        print(f"🖼️ Chemin du logo : {logo_path}")
        logo_base64 = encode_image_to_base64(logo_path)
        print("✅ Logo encodé en base64")

        base_url = get_base_url(request)
        file_url = f"{base_url.strip()}/fichiers/{filename}"
        print(f"🔗 URL du fichier : {file_url}")

        print("🎨 Génération du QR code...")
        qr_image = gr_code.generate_qr_base64(file_url)
        print("✅ QR code généré")

        print("📅 Traitement de la date...")
        try:
            # Convertir la date en UTC
            date_rdv_obj = await ensure_utc(parse_date_string(data.date_rdv))
            print(f"📅 Date convertie en UTC : {date_rdv_obj}")
        except ValueError as e:
            print(f"💥 ERREUR de format de date : {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Format de date invalide. Utilisez le format ISO (YYYY-MM-DDTHH:MM:SS)"
            )
        
        print(f"📅 Date formatée pour l'affichage : {date_rdv_obj.strftime('%d/%m/%Y')}")

        print("📝 Rendu du template HTML...")
        # 📝 Traitement des observations et préconisations (split sur '-')
        observations_list = [obs.strip() for obs in data.liste_observations.split('-') if obs.strip()]
        preconisations_list = [prec.strip() for prec in data.liste_preconisations.split('-') if prec.strip()]
        
        print(f"📋 Observations traitées: {len(observations_list)} éléments")
        print(f"📋 Préconisations traitées: {len(preconisations_list)} éléments")
        
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
            liste_observations=observations_list,
            liste_preconisations=preconisations_list,
            annee=date.today().year,
            base_url=base_dir,
            logo_base64=logo_base64,
            qr_code=qr_image
        )
        print("✅ Template HTML rendu avec succès")

        print("🖨️ Génération du PDF...")
        # 🖨️ Génération du PDF avec ta fonction existante
        file_infos = await generate_pdf_from_html(rendered_html, filename, request)
        print("✅ PDF généré avec succès")

        print("✨ Génération du compte rendu terminée avec succès!")
        return {
            "message": "✅ Compte rendu généré avec succès.",
            "filename": file_infos.get("filename"),
            "file_url": file_infos.get("file_url"),
            "file_encoded": f"data:application/pdf;base64,{file_infos.get('file_encoded')}"
        }
    except Exception as e:
        print(f"💥 ERREUR lors de la génération du compte rendu : {str(e)}")
        print(f"🔍 Détails de l'erreur : {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du compte rendu : {str(e)}"
        )



