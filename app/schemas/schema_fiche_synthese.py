from pydantic import BaseModel, Field
from typing import Optional

class FicheSyntheseInput(BaseModel):
    nom: str = Field(..., description="Nom du bénéficiaire")
    entreprise: str = Field(..., description="Nom de l'entreprise")
    date_creation: str = Field(..., description="Date de création de l'entreprise")
    nom_programme: str = Field(..., description="Nom du programme")
    adresse: str = Field(..., description="Adresse")
    prenom: str = Field(..., description="Prénom du bénéficiaire")
    siret: str = Field(..., description="Numéro SIRET")
    contact: str = Field(..., description="Contact (téléphone/email)")
    qpv: str = Field(..., description="QPV (Quartier Prioritaire de la Ville)")
    secteur: str = Field(..., description="Secteur d'activité")
    ca: str = Field(..., description="Chiffre d'affaires")
    description_activite: str = Field(..., description="Description de l'activité ou business modèle")
    prix_vente_unitaire: str = Field(..., description="Prix de vente unitaire")
    cout_revient_unitaire: str = Field(..., description="Coût de revient unitaire")
    couts_fixes: str = Field(..., description="Coûts fixes")
    couts_variables: str = Field(..., description="Coûts variables")
    seuil_rentabilite: str = Field(..., description="Nombre d'unités à vendre pour être rentable")
    marge_par_unite: str = Field(..., description="Marge par unité")
    photo_base64: str = Field(..., description="Photo du bénéficiaire encodée en base64")
    carte_base64: Optional[str] = Field(None, description="Image de la carte encodée en base64") 