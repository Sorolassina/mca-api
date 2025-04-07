import pandas as pd
from time import sleep
from app.services.service_qpv import verif_qpv  # Adapte ce chemin si nécessaire
from fastapi import  Request

async def recherche_groupqpv(input_path: str, output_path: str, file_type:str , request: Request):
    
    # 📥 Lire le fichier
    if file_type == "xlsx":
        df = pd.read_excel(input_path)
    elif file_type == "csv":
        df = pd.read_csv(input_path)
    else:
        raise ValueError("❌ Format de fichier non supporté.")

    
    # 📌 Vérification de la colonne d’adresse
    possible_columns = ["Adresse complete"]
    adresse_col = next((col for col in df.columns if col.strip().lower() in [c.lower() for c in possible_columns]), None)

    if not adresse_col:
        raise ValueError("❌ Le fichier doit contenir une colonne intitulée 'Adresse' ou 'Adresse complete'.")

    # Ajouter les colonnes de résultat
    df["nom_qpv"] = ""
    df["carte_qpv"] = ""
    df["distance_qpv_en_metre"] = ""

    # Traiter chaque ligne
    for index, row in df.iterrows():
        payload = {
            "address": row["Adresse complete"]
        }
        address = str(payload.get("address")) if payload.get("address") is not None else ""
        try:
            print(f"🔍 Envoi du payload à verif_qpv : {payload}")

            # 🔒 Vérification de la qualité du champ avant appel API
            if (
                not address or
                len(address) < 5 or
                len(address.split()) < 3
            ) :
                continue
                
            result = await verif_qpv(payload, request)  # appel direct à la fonction
            

            if result is None:
                raise ValueError(f"⚠️ Aucun résultat pour l'adresse : {payload['address']}")
            
            df.at[index, "nom_qpv"] = result.get("nom_qp", "")
            df.at[index, "carte_qpv"] = result.get("carte", "")
            df.at[index, "distance_qpv_en_metre"] = result.get("distance_m", "")

        except Exception as e:
            print(f"❌ Erreur ligne {index+1} : {e}")
            break  

        sleep(1)  # pause facultative

    # 💾 Sauvegarder les résultats
     # 💾 Export
    if file_type == "xlsx":
        df.to_excel(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)

    print(f"✅ Fichier avec résultats enregistré à : {output_path}")