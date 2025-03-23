from fastapi import  Request,Form,UploadFile, File,APIRouter,HTTPException
from fastapi.responses import RedirectResponse
from app.schemas.schema_qpv import Adresse  # Validation des données d'adresse
from app.schemas.schema_siret import SiretRequest  # Validation des données d'adresse
from app.schemas.schema_digiforma import DigiformaInput
from app.schemas.schema_Html import HTMLFileInput
from logs.errors import get_result_template
from pydantic import ValidationError
from datetime import date
import os
from fastapi.templating import Jinja2Templates
from app.services import service_digiforma,service_qpv,service_generate_pdf_from_file,service_siret_pappers
from app.utils.template import build_success_result_html

# ✅ Monter le dossier "templates" pour qu'il soit accessible via "/templates/"
templates_path = os.path.join(os.getcwd(), "app/templates")
templates = Jinja2Templates(directory=templates_path)

router = APIRouter()

@router.post("/process")
async def process_service(
    request: Request,
    service: str = Form(...),
    input_data: str = Form(""),
    latitude: float = Form(0.0),
    longitude: float = Form(0.0),
    html_content:str=Form(""),
    filename: str = Form("file_genered.pdf"),
    html_file: UploadFile = File(None)  # Ajout pour gérer l'upload de fichier
):
    
    try:
        if service == "pdf_from_html" and html_file is None:
            file_infos= await service_generate_pdf_from_file.generate_pdf_from_html(html_content, filename, request)

            filename= file_infos.get("filename",None)
            download_url=file_infos.get("file_url",None)
            message=f"Votre fichier {filename} est pêt."
            result = build_success_result_html(message=message, download_url=download_url, filename=filename)

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
            
        elif service == "check_qpv":
            print(f"DEBUG Je suis dans le check-qpv : {input_data}")
            adresse = Adresse(address=input_data, latitude=latitude, longitude=longitude)
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
        
    except ValidationError as ve:
        # Extraction des messages d'erreur Pydantic
        errors = ve.errors()
        error_messages = "<br>".join([f"{err['loc'][0]} : {err['msg']}" for err in errors])
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
    

    
