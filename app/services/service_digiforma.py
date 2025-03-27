import requests
from fastapi import HTTPException, Request
import pandas as pd
from app.config import DIGIFORMA_API_KEY 
import time
from datetime import date
import zipfile
import os

from app.config import get_base_url, FICHIERS_DIR
from app import config
from app.schemas.schema_digiforma import DigiformaInput
from app.utils.file_encoded import encode_file_to_base64

DIGIFORMA_GRAPHQL_URL = "https://app.digiforma.com/api/v1/graphql"

def digiforma_graphql_post(query: str, timeout: int = 50, debug: bool = False) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DIGIFORMA_API_KEY}"
    }

    payload = {"query": query}

    try:
        response = requests.post(DIGIFORMA_GRAPHQL_URL, json=payload, headers=headers, timeout=timeout)
        if debug:
            print(f"✅ [DEBUG] Digiforma response status: {response.status_code}")

        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise HTTPException(status_code=500, detail=f"❌ Erreur Digiforma : {result['errors'][0]['message']}")

        return result.get("data", {})

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à Digiforma : {str(e)}")

async def extract_digiforma_data(data: DigiformaInput,request:Request):
    """ 📌 Récupère les données de Digiforma et retourne un fichier ZIP contenant les CSV """
    start_date = date.today().strftime("%Y-01-01")
    try:
        
        query_test =  f""" 
            query {{ trainingSessions(filters: {{ startedAfter: "{start_date}" }})
                {{
                    id 
                }}
            }}"""    

        test_response = digiforma_graphql_post(query_test, debug=True)
        print("✅ DEBUG Test connexion réussi")
        
        # ✅ Requêtes GraphQL
        query_all_Session = f""" 
            query {{ trainingSessions(filters: {{ startedAfter: "{start_date}" }})
                {{
                    id name code pipelineState program {{ name trainingType  }}
                    trainees {{ firstname lastname civility handicaped grades{{scoreResult}} }}
                    dates {{ date endTime startTime  }}endDate
                    evaluationScore {{ totalScores {{ evaluationType score  }} }}
                 }}
            }}"""
       
        # ✅ Requête sessions
        dataSession = digiforma_graphql_post(query_all_Session, debug=True)

        # ✅ Vérification de la structure JSON
        if "trainingSessions" in dataSession:
            sessions = dataSession["trainingSessions"]
        else:
            raise HTTPException(status_code=500, detail="❌ Erreur : Structure de réponse incorrecte.")

        # ✅ Structuration des sessions
        sessions_data = []
        for session in sessions:
            data_ord = sorted(session["dates"], key=lambda d: d["date"])
            sessions_data.append({
                "Date de mise à jour": date.today(),
                "Id_session": session["id"],
                "Libelle session": session["name"],
                "Code": session["code"],
                "Pipeline": session["pipelineState"],
                "Programme": session["program"]["name"] if session.get("program") else "",
                "Date début": data_ord[0]["date"] if data_ord else None,
                "Date fin": session["endDate"],
                "Total score": next((round(ev["score"],2) for ev in session.get("evaluationScore", [{}])[0].get("totalScores", []) if ev["evaluationType"] == "TOTAL"), 0.0),
                "Total PRE": next((round(ev["score"],2) for ev in session.get("evaluationScore", [{}])[0].get("totalScores", []) if ev["evaluationType"] == "PRE"), 0.0),
                "Total HOT": next((round(ev["score"],2) for ev in session.get("evaluationScore", [{}])[0].get("totalScores", []) if ev["evaluationType"] == "HOT"), 0.0),
                "Total COLD": next((round(ev["score"],2) for ev in session.get("evaluationScore", [{}])[0].get("totalScores", []) if ev["evaluationType"] == "COLD"), 0.0),
                "Apprenants": ", ".join([f"{tr['firstname']} {tr['lastname']}" for tr in session.get("trainees", [])])
            })

        # ✅ Requête trainees (Pause pour éviter le throttling)
        time.sleep(5)

        query_all_Trainee = """ 
            query { customers {
                customerTrainees {
                    trainee { id civility firstname lastname handicaped }         
                    passed sessionCompletion signatures {
                        signature type dates { date slot subsession { name id } }
                    }
                }               
                trainingSession { id name code }
            }}
        """   
        dataCustomers = digiforma_graphql_post(query_all_Trainee, debug=True) 

        if "customers" in dataCustomers:
            customers = dataCustomers["customers"]
        else:
            raise HTTPException(status_code=500, detail="❌ Erreur : Structure de réponse incorrecte.")

        # ✅ Extraction des trainees
        customer_trainees_data = []
        for customer in customers:  # Parcourir chaque client
            trainingSession = customer.get("trainingSession", {})  # Récupérer la session
            session_id = trainingSession.get("id", "")
            session_name = trainingSession.get("name", "")
            session_code = trainingSession.get("code", "")

            for trainee in customer.get("customerTrainees", []):  # Parcourir chaque trainee
                T = trainee.get("trainee", {})  # Récupérer trainee info

                # Vérifier s'il y a des signatures et des dates associées
                if "signatures" in trainee and trainee["signatures"]:
                    for signature in trainee["signatures"]:
                        for date_info in signature.get("dates", []):
                            customer_trainees_data.append({
                                "Date de mise à jour": date.today(),
                                "Id_session": session_id,
                                "Nom_session": session_name,
                                "Code_session": session_code,
                                "Id_trainee": T.get("id", ""),
                                "Civility": T.get("civility", ""),
                                "Nom Trainee": T.get("lastname", ""),
                                "Prénom Trainee": T.get("firstname", ""),
                                "Handicapé": T.get("handicaped", False),
                                "Réussite": trainee.get("passed", False),
                                "Completion Session": trainee.get("sessionCompletion", 0),
                                "Signature": signature.get("signature", ""),
                                "Type Signature": signature.get("type", ""),
                                "Date Signature": date_info.get("date", ""),
                                "Slot Signature": date_info.get("slot", ""),
                                "Sous-session": date_info.get("subsession", {}).get("name", ""),
                                "Id Sous-session": date_info.get("subsession", {}).get("id", ""),
                            })
                else:
                    # Ajouter une ligne même s'il n'y a pas de signature
                    customer_trainees_data.append({
                        "Date de mise à jour": date.today(),
                        "Id_session": session_id,
                        "Nom_session": session_name,
                        "Code_session": session_code,
                        "Id_trainee": T.get("id", ""),
                        "Civility": T.get("civility", ""),
                        "Nom Trainee": T.get("lastname", ""),
                        "Prénom Trainee": T.get("firstname", ""),
                        "Handicapé": T.get("handicaped", False),
                        "Réussite": trainee.get("passed", False),
                        "Completion Session": trainee.get("sessionCompletion", 0),
                        "Signature": "",
                        "Type Signature": "",
                        "Date Signature": "",
                        "Slot Signature": "",
                        "Sous-session": "",
                        "Id Sous-session": "",
                    })
        # ✅ Création des DataFrames
        df_customers = pd.DataFrame(customer_trainees_data)
        df_sessions = pd.DataFrame(sessions_data)

        # ✅ Sauvegarde en CSV
        customer_file = "df_customer_trainees_data.csv"
        session_file = "df_sessions.csv"

        df_customers.to_csv(customer_file, index=False)
        df_sessions.to_csv(session_file, index=False)

        # ✅ Création du ZIP
        zip_url = os.path.join(FICHIERS_DIR, "exported_files.zip")

        with zipfile.ZipFile(zip_url, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(customer_file)
            zipf.write(session_file)

         # Vérifie si l’image existe avant d’essayer de l’encoder
        if os.path.exists(zip_url):
            zip_content_base64 = encode_file_to_base64(zip_url)
        else:
            zip_content_base64 = None  # Si l’image n’existe pas

        # ✅ Suppression des fichiers CSV après création du ZIP
        os.remove(customer_file)
        os.remove(session_file)
        
        base_url = get_base_url(request)  # Récupérer l'URL dynamique
        
        # ✅ Retour du fichier ZIP à Power Automate
        # ✅ Réponse JSON contenant la base64 du ZIP
        return {
        "filename": "exported_files.zip",
        "download_url": f"{base_url}/fichiers/exported_files.zip",
        "content_base64": zip_content_base64
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à Digiforma : {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Erreur interne : {str(e)}")