from fastapi import  Request,Form,UploadFile, File,APIRouter,HTTPException
from fastapi.responses import RedirectResponse
from app.schemas.schema_qpv import Adresse  # Validation des données d'adresse
from app.schemas.schema_siret import SiretRequest  # Validation des données d'adresse
from app.schemas.schema_digiforma import DigiformaInput
from app.schemas.schema_Html import HTMLFileInput
from app.logs.errors import get_result_template
from pydantic import ValidationError
from datetime import date
import os
from fastapi.templating import Jinja2Templates
from app.services import service_digiforma,service_qpv,service_generate_pdf_from_file,service_siret_pappers
from app.utils.template import build_success_result_html
from fastapi import UploadFile
import aiofiles
from app.config import  FICHIERS_DIR,  TEMPLATE_DIR
from app.utils.traiter_zip_excel import traiter_zip_entier  # ajuste selon ton arborescence
import shutil
from app.utils.temp_dir import create_temp_file, delete_temp_dir
from app.services.service_QPV_QueryGroup import recherche_groupqpv

# ✅ Monter le dossier "templates" pour qu'il soit accessible via "/templates/"

templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter()

@router.post("/process")
async def process_service(
    request: Request,
    service: str = Form(...),
    input_data: str = Form(""),
    html_content:str=Form(""),
    custom_file: UploadFile = File(...),
    old_words: str = Form(""),
    filename: str = Form("file_genered.pdf"),
    new_word: str = Form(""),
    html_file: UploadFile = File(None)  # Ajout pour gérer l'upload de fichier
):
    
    try:
        if service == "pdf_from_html" and html_file is None:
            file_infos= await service_generate_pdf_from_file.generate_pdf_from_html(html_content, filename, request)

            filename= file_infos.get("filename",None)
            download_url=file_infos.get("file_url",None)
            message=f"Votre fichier {filename} est pêt."
            result = build_success_result_html(
                                                message=message,
                                                download_url=download_url,
                                                filename=filename
                                            )

            request.session["result"] = result
            request.session["download_url"] = download_url
            return RedirectResponse(url="/", status_code=303)
        
        elif service == "pdf_from_html" and html_file is not None:
                       
            # 🔹 Récupérer le nom de fichier sans son extension et ajouter `.pdf`
            base_filename = os.path.splitext(html_file.filename)[0]  # Extrait le nom sans l'extension
            filename = f"{base_filename}.pdf"  # Remplace l'extension

            # Lire le contenu du fichier
            file_content = await html_file.read()
            
            # Vérifier que le contenu est bien du HTML en utilisant notre modèle Pydantic
            decoded_content = file_content.decode("utf-8", errors="ignore")
            
            if not decoded_content.strip():
                raise HTTPException(status_code=400, detail="Le fichier HTML est vide après décodage.")
            try:
                
                validated_data = HTMLFileInput(
                    filename=html_file.filename, 
                    content=decoded_content
                )

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
    
            file_infos = await service_generate_pdf_from_file.generate_pdf_from_html(validated_data.content,filename,request)

            filename= file_infos.get("filename",None)
            download_url=file_infos.get("file_url",None)
            message=f"Votre fichier {filename} est pêt."
            result = build_success_result_html(message=message, download_url=download_url, filename=filename)

            request.session["result"] = result
            request.session["download_url"] = download_url
            return RedirectResponse(url="/", status_code=303)    
        
        elif service == "digiformat_data":
            # Validation Pydantic
            entreprise_infos = await service_digiforma.extract_digiforma_data(DigiformaInput(Password=input_data), request) 
            
            filename= entreprise_infos.get("filename",None)
            download_url=entreprise_infos.get("download_url",None)
            message=f"Votre dossier {filename} est pêt."
            result = build_success_result_html(message=message, download_url=download_url, filename=filename)
            request.session["result"] = result
            request.session["download_url"] = download_url

            return RedirectResponse(url="/", status_code=303)

        elif service == "company_info":
            # Validation Pydantic
            siret_obj = SiretRequest(numero_siret=input_data)
            # Extraire les 9 premiers chiffres seulement si c’est valide
            numero_siret = siret_obj.numero_siret[:9]
            etat_qpv= await service_siret_pappers.get_entreprise_process(numero_siret, request) 
  
            message=etat_qpv.get("message",None)
            download_url=etat_qpv.get("download_url",None)
            result = build_success_result_html(message=message, download_url=download_url, filename=input_data)
        
            request.session["result"] = result
            request.session["download_url"] = download_url
            return RedirectResponse(url="/", status_code=303)

        elif service == "customize_folder":
    
            if not custom_file or not new_word or not old_words:
                raise HTTPException(status_code=400, detail="Fichier, nouveau et anciens mots requis.")

            old_words_list = [w.strip() for w in old_words.split(",") if w.strip()]
            replacements = {word: new_word for word in old_words_list}

            # Enregistrer temporairement le fichier reçu
            temp_dir, input_path=create_temp_file(custom_file.filename)

            async with aiofiles.open(input_path, "wb") as out_file:
                content = await custom_file.read()
                await out_file.write(content)

            # ⚙️ Appel à la nouvelle fonction          
            try:
                final_zip, ignored = traiter_zip_entier(input_path, replacements)
                 
            except Exception as e:
                msg = f"❌ Erreur pendant le traitement du fichier : {str(e)}"
                request.session["result"] = get_result_template(msg, type_="error")
                delete_temp_dir(temp_dir)
                return RedirectResponse(url="/", status_code=303)

            filename = os.path.basename(final_zip)  # ✅ Extrait uniquement "monfichier.zip"
            final_path = os.path.join(FICHIERS_DIR, filename)  # ✅ Construit le chemin final dans ton dossier static
            shutil.copy(final_zip, final_path)  # ✅ Copie le fichier vers static/fichiers/
            download_url = f"/static/fichiers/{filename}"  # ✅ URL publique à retourner pour téléchargement

            # ✅ Message HTML final
            message = f"✅ Le fichier personnalisé <b>{filename}</b> est prêt au téléchargement."

            # Tu peux ajouter ici la gestion des fichiers ignorés si tu veux
            result = build_success_result_html(
                                                message=message,
                                                download_url=download_url,
                                                filename=filename,
                                                ignored_list=ignored  # si cette variable existe
                                            )
            
            request.session["result"] = result
            request.session["download_url"] = download_url
            delete_temp_dir(temp_dir)
            return RedirectResponse(url="/", status_code=303)

        elif service == "check_qpv":
            
            adresse = Adresse(address=input_data)
            qpv_data = await service_qpv.verif_qpv(adresse.model_dump(), request)
            map_url = qpv_data.get("carte", None)
            nom_qpv = qpv_data.get("nom_qp", None)
            distance_qpv = qpv_data.get("distance_m", None)
            image_url=qpv_data.get("image_url", None)
            download_url = image_url

            result = f"""
                <div style="
                    background-color: rgba(255, 255, 255, 0.3);
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                    text-align: left;
                    width: 400px;
                    margin: 20px auto;">
                    📅 Aujourd'hui : {date.today().strftime("%d/%m/%Y")}<br>
                    📍 <b>{input_data}</b><br>
                    ✅ {nom_qpv}<br>
                    📏 Distance : {distance_qpv} mètres <br>
                    🔗 <a href="{map_url}" target="_blank" style="color:blue; text-decoration:none;">
                        Cliquer ici pour visualiser
                        </a>
                </div>
            """   
            request.session["result"] = result
            request.session["download_url"] = download_url
            
            return RedirectResponse(url="/", status_code=303)
        
        elif service == "check_groupeqpv" and html_file is not None:

            # ✅ Vérification du type de fichier
            ALLOWED_EXTENSIONS = [".xlsx", ".csv"]
            filename = html_file.filename
            if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                msg = "❌ Erreur : Seuls les fichiers Excel (.xlsx) sont autorisés pour ce service."
                request.session["result"] = get_result_template(msg, type_="error")
                return RedirectResponse(url="/", status_code=303)
    
            # Enregistrer le fichier temporairement
            temp_dir, input_path=create_temp_file(html_file.filename)

            print(f"✅ DEBUG Input path : {input_path}")
            async with aiofiles.open(input_path, "wb") as f:
                content = await html_file.read()
                await f.write(content)

            

            if filename.lower().endswith(".xlsx"):
                output_path = os.path.join(FICHIERS_DIR, "resultats_qpv.xlsx")
                type="xlsx"
            else :
                output_path = os.path.join(FICHIERS_DIR, "resultats_qpv.xlsx")
                type="csv"

            await recherche_groupqpv(input_path, output_path, type, request)

            message = "✅ Le fichier avec les résultats QPV est prêt."
            result = build_success_result_html(message, download_url="/static/fichiers/resultats_qpv.xlsx", filename="resultats_qpv.xlsx")
            request.session["result"] = result

            delete_temp_dir(temp_dir)
            return RedirectResponse(url="/", status_code=303)
        
    except ValidationError as ve:
        # Extraction des messages d'erreur Pydantic
        errors = ve.errors()
        error_messages = "<br>".join([
                f"{'.'.join(map(str, err.get('loc', [])))} : {err.get('msg', 'Erreur inconnue')}"
                for err in errors
            ])
        request.session["result"] = get_result_template(f"❌ Erreur de validation :<br>{error_messages}", type_="error")

    except TypeError as e:
        if "argument after ** must be a mapping" in str(e):
            msg = "❌ Erreur : Les données envoyées ne sont pas au bon format. Il faut un objet JSON avec les bonnes clés."
        else:
            msg = f"❌ Erreur technique : {str(e)}"
        request.session["result"] = get_result_template(msg, type_="error")

    except Exception as e:
        request.session["result"] = get_result_template(f"❌ Erreur inattendue : {str(e)}", type_="error")

    return RedirectResponse(url="/", status_code=303)
    

    
