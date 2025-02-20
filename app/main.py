from fastapi import FastAPI,APIRouter, Depends, HTTPException
from app.routes import route_generate_pdf_from_html, route_qpv, route_siret_pappers
from app.security.auth import router as auth_router, oauth2_scheme, verify_token, get_user
from fastapi.staticfiles import StaticFiles
import os
from fastapi.responses import RedirectResponse


app = FastAPI(
    title="Mon API FastAPI 🚀", 
    description="Gestion de candidats entrepreneurs",
    version="1.0.0",
    openapi_url="/api-mca/v1/mycreo.json",  # Personnalise l'endpoint OpenAPI
    docs_url="/api-mca/v1/recherche",  # Personnalise l'URL de Swagger UI,
    redoc_url="/api-mca/v1/documentation"  # Personnalise l'URL de ReDoc
    )

# ✅ Vérification globale de l'authentification
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return user  # Retourne les infos de l'utilisateur

# ✅ Groupe de routes sécurisé
api_router = APIRouter(
    prefix="/api-mca/v1",
    dependencies=[Depends(get_current_user)]  # 🔥 Sécurise tout le groupe !
)

# Monter le dossier static pour que FastAPI puisse y accéder
app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "app/static")), name="static")



@app.get("", tags=["Root"])  # 🔥 Permet d'accéder sans "/" final
@app.get("/", tags=["Root"])
def read_root():
    return RedirectResponse(url="/api-mca/v1/documentation", status_code=307)

# Inclusion des routes
api_router.include_router(route_generate_pdf_from_html.router, tags=["Génération de PDF à partir de HTML"])
api_router.include_router(route_siret_pappers.router, tags=["siret"])
api_router.include_router(route_qpv.router, tags=["qpv"])
api_router.include_router(auth_router)

# ✅ Ajouter toutes les routes sous "/api-mca/v1"
app.include_router(api_router) 

#for route in app.router.routes:
    #print(f"➡️ {route.path} ({route.name})")