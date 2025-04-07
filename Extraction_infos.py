import pandas as pd
import requests
import csv

# Exemple de fonction corrigée : lecture d'un CSV contenant des SIRET, appel à Pappers pour chacun, sauvegarde en CSV
def get_entreprise_process(csv_input_path, csv_output_path, api_key):
    # Lire les données avec les SIRET
    df = pd.read_excel(csv_input_path)
    
    # S'assurer que la colonne SIRET existe
    if "SIRET" not in df.columns:
        raise ValueError("La colonne 'SIRET' est manquante dans le fichier CSV.")
    
    # Initialiser les lignes de sortie
    lignes_csv = []

    # Pour chaque SIRET du fichier
    for numero_siret in df["SIRET"].dropna().astype(str):
        siren = numero_siret[:9]
        url = f"https://api.pappers.fr/v2/entreprise?siren={siren}&api_token={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Vérifier si les comptes existent
            comptes = data.get("comptes", [])
            comptes_disponibles = [compte for compte in comptes if compte.get("nom_fichier_pdf")]

            if not comptes_disponibles:
                comptes_disponibles = [{}]  # ajouter ligne vide si pas de comptes

            for compte in comptes_disponibles:
                lignes_csv.append([
                    data.get("nom_entreprise", "N/A"),
                    data.get("siren", "N/A"),
                    data.get("siege", {}).get("adresse", "N/A"),
                    data.get("effectif", "N/A"),
                    data.get("date_creation", "N/A"),
                    data.get("code_naf", "N/A"),
                    data.get("activite", "N/A"),
                    compte.get("annee_cloture", "N/A"),
                    compte.get("date_depot_formate", "N/A"),
                    compte.get("type_comptes", "N/A"),
                    compte.get("nom_fichier_pdf", "N/A"),
                    compte.get("token", "N/A")
                ])
        except Exception as e:
            lignes_csv.append([numero_siret, "Erreur", str(e)])

    # Sauvegarder en CSV
    with open(csv_output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Nom_Entreprise", "Siret", "Adresse", "Effectif",
            "Date_Creation", "Code_NAF", "Activite",
            "Année clôture", "Date_depot", "Type_comptes",
            "Nom_fichier_PDF", "Tokens"
        ])
        writer.writerows(lignes_csv)

    return f"Fichier généré : {csv_output_path}"

# Exemple d'appel (à adapter en local avec chemins réels)
exemple_resultat = get_entreprise_process(
    csv_input_path="C:/Users/SOROLASSINA/Downloads/Candidats jury.xlsx",
    csv_output_path="C:/Users/SOROLASSINA/Downloads/Candidats.csv",
    api_key="3721812f3ce2b994725e057e906fe35a96ec4ee4209da3f2"
)

exemple_resultat
