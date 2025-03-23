from datetime import date

def build_success_result_html(message: str, download_url: str, filename: str = None) -> str:
    """
    Génère un bloc HTML stylisé pour un message de succès avec lien de téléchargement.
    """
    today = date.today().strftime("%d/%m/%Y")
    filename_info = f"<b>{filename}</b><br>" if filename else ""

    return f"""
        <div style="
            background-color: rgba(255, 255, 255, 0.3);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
            text-align: left;
            width: 400px;
            margin: 20px auto;">
            📅 Aujourd'hui : {today}<br>
            ✅ {filename_info}{message}<br>
            🔗 <a href="{download_url}" target="_blank" style="color:blue; text-decoration:none;">
                Cliquer ici pour afficher le fichier
            </a>
        </div>
    """
