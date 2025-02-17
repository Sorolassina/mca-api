from fastapi import APIRouter
from app.models.item import Item

router = APIRouter()

# Endpoint pour récupérer tous les items
@router.get("/items")
def get_items():
    return [{"id": 1, "name": "Ordinateur"}, {"id": 2, "name": "Smartphone"}]

# Endpoint pour créer un nouvel item
@router.post("/items")
def create_item(item: Item):
    return {"message": "Item ajouté avec succès", "item": item}
