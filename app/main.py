from fastapi import FastAPI,APIRouter
from app.routes import route_generate_pdf_from_html, route_qpv, route_siret_pappers
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

# ✅ Créer un routeur pour tout regrouper sous "/api-mca/v1"
api_router = APIRouter(prefix="/api-mca/v1")

# Monter le dossier static pour que FastAPI puisse y accéder
app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "app/static")), name="static")

# Inclusion des routes
api_router.include_router(route_generate_pdf_from_html.router, tags=["Génération de PDF à partir de HTML"])
api_router.include_router(route_siret_pappers.router, tags=["siret"])
api_router.include_router(route_qpv.router, tags=["qpv"])

@api_router.get("", tags=["Root"])  # 🔥 Permet d'accéder sans "/" final
@api_router.get("/", tags=["Root"])
def read_root():
    return RedirectResponse(url="/api-mca/v1/documentation", status_code=307)

# ✅ Ajouter toutes les routes sous "/api-mca/v1"
app.include_router(api_router) 

for route in app.router.routes:
    print(f"➡️ {route.path} ({route.name})")