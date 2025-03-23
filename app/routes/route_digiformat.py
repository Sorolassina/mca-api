
from fastapi import APIRouter, HTTPException, Request
from app.services.service_digiforma import extract_digiforma_data
from app.schemas.schema_digiforma import DigiformaInput
router = APIRouter()

@router.post("/digiforma")
async def get_digiforma_sessions(data:DigiformaInput, request:Request):
    try:
        return await extract_digiforma_data(data,request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Erreur interne : {str(e)}")


