from pydantic import BaseModel,model_validator
import requests

class Adresse(BaseModel): #Modèle pydantic pour la validation de l'adresse transmise
    address: str
    latitude: float = None
    longitude: float = None
    
    model_config = {"frozen": False}  # ✅ autorise la modification dans le validateur

    @model_validator(mode="after")
    def validate_address(self):
        
        address=self.address
        url = f"https://api-adresse.data.gouv.fr/search/?q={address.replace(' ', '+')}" 
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Lève une erreur si la requête échoue
            data = response.json() # Vérifier si la réponse est bien un JSON
        
            # Vérifier si des résultats existent
            if data.get("features") : #and data['features'][0]['properties'].get('score', 0)>0.8:
                # Extraire les coordonnées GPS
                coords = data["features"][0]["geometry"]["coordinates"]
                # ✅ on retourne une copie mise à jour
                return self.model_copy(update={
                    "latitude": coords[1],
                    "longitude": coords[0]
                })              
                
            else :
                raise ValueError("Coordonnées non trouvées et/ou adresse non précise.")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Erreur API : {str(e)}")
    