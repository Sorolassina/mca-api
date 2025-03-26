from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
import os
import asyncio
import uvicorn
from fastapi.templating import Jinja2Templates
from app.config import BASE_DIR
from contextlib import asynccontextmanager
from app.utils.cleanup_scheduler import start_cleanup_scheduler, stop_cleanup_scheduler
from starlette.middleware.sessions import SessionMiddleware
from app.routes import route_rdv, route_generate_pdf_from_html, route_qpv, route_siret_pappers, route_digiformat, route_service_interface
from fastapi.responses import FileResponse

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_cleanup_scheduler()
    yield
    stop_cleanup_scheduler()

# ✅ Création de l'application FastAPI
app = FastAPI(
    title="Mon API FastAPI 🚀",
    description="Gestion de candidats entrepreneurs",
    version="1.0.0",
    openapi_url="/api-mca/v1/mycreo.json",  # Personnalisation de l'endpoint OpenAPI
    docs_url="/api-mca/v1/recherche",  # Personnalisation de l'URL de Swagger UI
    redoc_url="/api-mca/v1/documentation",  # Personnalisation de l'URL de ReDoc
    lifespan=lifespan
)

# ✅ Middleware pour les sessions (affichage résultat après redirection)
app.add_middleware(SessionMiddleware, secret_key="une-cle-secrete-tres-longue")


# ✅ Définition d'un groupe de routes sécurisé
api_router = APIRouter(prefix="/api-mca/v1")

# ✅ Monter le dossier "templates" pour qu'il soit accessible via "/templates/"
templates_path = os.path.join(os.getcwd(), "app/templates")
templates = Jinja2Templates(directory=templates_path)

# ✅ Monter le dossier "static" et fichier pour qu'il soit accessible via "/static/"
static_path = os.path.join(os.getcwd(), "app/static")
app.mount("/static", StaticFiles(directory=static_path), name="static")
app.mount("/fichiers", StaticFiles(directory=os.path.join(BASE_DIR, "..", "fichiers")), name="fichiers")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

# ✅ Redirection de la racine vers la documentation
@app.get("/", tags=["Root"])
@app.head("/")  # Autoriser HEAD sur "/"
def read_root(request: Request):
    result = request.session.pop("result", None)
    download_url = request.session.pop("download_url", None)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documentation": "/api-mca/v1/documentation",
        "url_process": "/api-mca/v1/process",
        "result": result,
        "download_url": download_url
    })

@app.get("/ping")
async def ping():
    return {"status": "ok"}  # Réponse minimale


# ✅ Inclusion des routes dans l'API
api_router.include_router(route_generate_pdf_from_html.router, tags=["Génération de PDF à partir de HTML"])
api_router.include_router(route_siret_pappers.router, tags=["Siret"])
api_router.include_router(route_qpv.router, tags=["QPV"])
api_router.include_router(route_digiformat.router, tags=["Digiformat"])
api_router.include_router(route_rdv.router, tags=["Rendez-vous"])
api_router.include_router(route_service_interface.router, tags=["Service Interface"])

# ✅ Ajouter toutes les routes sous "/api-mca/v1"
app.include_router(api_router)

# ✅ Lancement du serveur si le script est exécuté directement
if __name__ == "__main__":
    try:
        # Ouvrir automatiquement le navigateur sur l'API
        port = int(os.environ.get("PORT", 8080))  # 8080 si non défini
        asyncio.run(uvicorn.run("main:app", host="0.0.0.0", port=port))
    except asyncio.CancelledError:
        print("❌ Interruption détectée, arrêt propre du serveur...")


