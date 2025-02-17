from pydantic import BaseModel, validator, Field

# Définition du modèle de requête avec Pydantic
class HTMLInput(BaseModel):
    html_content: str = Field(..., title="Contenu HTML à convertir en PDF")
    filename: str = Field("document.pdf", title="Nom du fichier PDF généré")

class HTMLFileInput(BaseModel):
    content: str
    filename: str = Field("document.pdf", title="Nom du fichier PDF généré")

    

    @validator("filename")
    def validate_filename(cls, v):

        """Vérifie si le nom de fichier se termine par .html ou .htm."""
        if not v.lower().endswith((".html", ".htm")):
            raise ValueError("Le fichier doit avoir une extension .html ou .htm.")
        return v
    
    @validator("content")
    def validate_html(cls, v):
        """
        Vérifie si le contenu contient bien des balises HTML.
        """
        if not ("<html" in v.lower() or "<body" in v.lower()):
            raise ValueError("Le fichier ne contient pas de balises HTML valides.")
        return v