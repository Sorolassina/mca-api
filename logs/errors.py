from fastapi.responses import JSONResponse

def error_response(code="INTERNAL_ERROR", message="Une erreur est survenue", details=None, status_code=500):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        }
    )

def get_result_template(message: str, type_: str = "success") -> str:
    """
    Génère un bloc HTML stylisé pour les messages à afficher dans l'interface.

    Args:
        message (str): Le contenu du message à afficher.
        type_ (str): Le type de message ('success', 'error', 'info'). Défaut : 'success'.

    Returns:
        str: Le HTML prêt à être affiché.
    """
    colors = {
        "success": "rgba(240, 255, 240, 0.9)",  # Vert clair
        "error": "#fff0f0",                    # Rouge clair
        "info": "#f0f8ff"                      # Bleu clair
    }

    text_colors = {
        "success": "green",
        "error": "red",
        "info": "#007BFF"
    }

    background = colors.get(type_, "#ffffff")
    color = text_colors.get(type_, "#000000")

    return f"""
        <div style="
            background-color: {background};
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-weight: bold;
            color: {color};
            font-size: 14px;
            width: 420px;
            margin-left:auto;
            margin-right:auto;">
            {message}
        </div>
    """
