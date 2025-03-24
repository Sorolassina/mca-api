import pandas as pd
import requests
from time import sleep

# 📥 Charger le fichier CSV avec les adresses
df = pd.read_excel("dataset.xlsx", sheet_name="Dataset")

# 🔧 URL de ton API (à adapter)
API_URL = "http://127.0.0.1:8080/api-mca/v1/qpv_check"

# 🛑 Ajoute deux colonnes pour les résultats
df["nom_qpv"] = ""
df["carte_qpv"] = ""

# 🔁 Parcourir chaque ligne
for index, row in df.iterrows():
    adresse_payload = {
        "address": row["Adresse complete"],
        "latitude": 0,
        "longitude": 0
    }
    print("📦 Payload envoyé :", adresse_payload)
    try:
        response = requests.post(API_URL, json=adresse_payload)

        if response.status_code == 200:
            result = response.json()
            df.at[index, "nom_qpv"] = result.get("nom_qp", "")
            df.at[index, "carte_qpv"] = result.get("carte", "")
        else:
            print(f"⚠️ Adresse ligne {index+1} rejetée (code {response.status_code})")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur à la ligne {index+1} : {e}")

    print(f"DEBUG Nom_qpv : {result.get("nom_qp", "")}")
    # Optionnel : petite pause pour ne pas spammer l'API
    sleep(1)

# 💾 Sauvegarder le résultat dans un nouveau fichier
df.to_excel("resultats_qpv.xlsx", index=False)
print("✅ Fichier avec résultats QPV généré : adresses_resultats_qpv.csv")
