from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import asyncio
import webbrowser
import uvicorn


# Importation des routes
from app.routes import route_generate_pdf_from_html, route_qpv, route_siret_pappers, route_digiformat

from middlewares import request_logger_middleware, error_handling_middleware, auth_middleware

# ✅ Création de l'application FastAPI
app = FastAPI(
    title="Mon API FastAPI 🚀",
    description="Gestion de candidats entrepreneurs",
    version="1.0.0",
    openapi_url="/api-mca/v1/mycreo.json",  # Personnalisation de l'endpoint OpenAPI
    docs_url="/api-mca/v1/recherche",  # Personnalisation de l'URL de Swagger UI
    redoc_url="/api-mca/v1/documentation"  # Personnalisation de l'URL de ReDoc
)

# ✅ Ajouter les middlewares
app.middleware("http")(request_logger_middleware)
app.middleware("http")(error_handling_middleware)
app.middleware("http")(auth_middleware)

# ✅ Définition d'un groupe de routes sécurisé
api_router = APIRouter(prefix="/api-mca/v1")

# ✅ Monter le dossier "static" pour qu'il soit accessible via "/static/"
static_path = os.path.join(os.getcwd(), "app/static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# ✅ Redirection de la racine vers la documentation
@app.get("/", tags=["Root"])
@app.head("/")  # Autoriser HEAD sur "/"
def read_root():
    return RedirectResponse(url="/api-mca/v1/documentation", status_code=307)

# ✅ Inclusion des routes dans l'API
api_router.include_router(route_generate_pdf_from_html.router, tags=["Génération de PDF à partir de HTML"])
api_router.include_router(route_siret_pappers.router, tags=["Siret"])
api_router.include_router(route_qpv.router, tags=["QPV"])
api_router.include_router(route_digiformat.router, tags=["Digiformat"])

# ✅ Ajouter toutes les routes sous "/api-mca/v1"
app.include_router(api_router)

# ✅ Lancement du serveur si le script est exécuté directement
if __name__ == "__main__":
    try:
        # Ouvrir automatiquement le navigateur sur l'API
        webbrowser.open("http://localhost:8000/")
        asyncio.run(uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True))
    except asyncio.CancelledError:
        print("❌ Interruption détectée, arrêt propre du serveur...")


