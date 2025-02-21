
from pydantic import BaseModel

# 📌 Définition du modèle Pydantic pour valider les données envoyées dans le body
class SiretRequest(BaseModel):
    numero_siret: str