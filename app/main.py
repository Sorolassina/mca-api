from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
import os
import asyncio
import uvicorn
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.utils.cleanup_scheduler import start_cleanup_scheduler, stop_cleanup_scheduler
from starlette.middleware.sessions import SessionMiddleware
from app.routes import route_rdv, route_generate_pdf_from_html, route_qpv, route_siret_pappers, route_digiformat, route_service_interface
from app.config import BASE_DIR,FICHIERS_DIR,STATIC_IMAGES_DIR, STATIC_MAPS_DIR,STATIC_DIR, TEMPLATE_DIR
# Dans app/main.py, ajouter :
from app.routes.forms import  route_emargement,route_evenement, route_preinscription, route_inscription, route_besoins, route_satisfaction
# Dans app/main.py, ajouter :
from app.routes import route_programme
from alembic.config import Config
from alembic import command
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import setup_logging
from sqlalchemy import text
from app.database import AsyncSessionLocal
import traceback


# Configuration du logging
logger = setup_logging()

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire de cycle de vie de l'application.
    Initialise les services au démarrage et les nettoie à l'arrêt.
    """
    print("\n🚀 === DÉMARRAGE DE L'APPLICATION ===")
    try:
        # Vérification des dossiers
        print("\n📁 Vérification des dossiers...")
        for directory in [STATIC_DIR, TEMPLATE_DIR, FICHIERS_DIR, STATIC_IMAGES_DIR, STATIC_MAPS_DIR]:
            if directory.exists():
                print(f"✅ Dossier {directory.name} trouvé")
            else:
                print(f"⚠️ Création du dossier {directory.name}")
                directory.mkdir(parents=True, exist_ok=True)

        # Test de la connexion à la base de données
        print("\n🔌 Test de la connexion à la base de données...")
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                print("✅ Connexion à la base de données réussie")
        except Exception as e:
            print(f"❌ Erreur de connexion à la base de données: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

        # Initialisation des migrations
        print("\n🔄 Initialisation des migrations de la base de données...")
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            print("✅ Migrations de la base de données terminées avec succès")
        except Exception as e:
            print(f"❌ Erreur lors des migrations: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

        # Démarrage du planificateur de nettoyage
        print("\n🧹 Démarrage du planificateur de nettoyage...")
        start_cleanup_scheduler()
        print("✅ Planificateur de nettoyage démarré")

        print("\n✨ Application prête à recevoir des requêtes !")
        print("=== FIN DÉMARRAGE ===\n")
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE AU DÉMARRAGE: {str(e)}")
        print(f"📋 Traceback complet:\n{traceback.format_exc()}")
        raise
    
    yield
    
    print("\n🛑 === ARRÊT DE L'APPLICATION ===")
    try:
        print("\n🧹 Arrêt du planificateur de nettoyage...")
        stop_cleanup_scheduler()
        print("✅ Planificateur de nettoyage arrêté")
        print("\n👋 Application arrêtée proprement")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'arrêt: {str(e)}")
    print("=== FIN ARRÊT ===\n")

# ✅ Création de l'application FastAPI
print("\n🎨 Création de l'application FastAPI...")
app = FastAPI(
    title="Mon API FastAPI 🚀",
    description="Gestion de candidats entrepreneurs",
    version="1.0.0",
    openapi_url="/api-mca/v1/mycreo.json",  # Personnalisation de l'endpoint OpenAPI
    docs_url="/api-mca/v1/recherche",  # Personnalisation de l'URL de Swagger UI
    redoc_url="/api-mca/v1/documentation",  # Personnalisation de l'URL de ReDoc
    lifespan=lifespan
)
print("✅ Application FastAPI créée")

# ✅ Middleware pour les sessions
print("\n🔐 Configuration des middlewares...")
app.add_middleware(SessionMiddleware, secret_key="une-cle-secrete-tres-longue")
print("✅ Middleware de session ajouté")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À modifier en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("✅ Middleware CORS ajouté")

# ✅ Définition des routes
print("\n🛣️ Configuration des routes...")
api_router = APIRouter(prefix="/api-mca/v1")
templates = Jinja2Templates(directory=TEMPLATE_DIR)
print("✅ Templates configurés")

# ✅ Montage des dossiers statiques
print("\n📂 Montage des dossiers statiques...")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/fichiers", StaticFiles(directory=FICHIERS_DIR), name="static")
print("✅ Dossiers statiques montés")

# ✅ Inclusion des routes
print("\n🔗 Inclusion des routes...")
api_router.include_router(route_generate_pdf_from_html.router, tags=["Génération de PDF à partir de HTML"])
api_router.include_router(route_siret_pappers.router, tags=["Siret"])
api_router.include_router(route_qpv.router, tags=["QPV"])
api_router.include_router(route_digiformat.router, tags=["Digiformat"])
api_router.include_router(route_rdv.router, tags=["Rendez-vous"])
api_router.include_router(route_service_interface.router, tags=["Service Interface"])
api_router.include_router(route_preinscription.router, prefix="/preinscription", tags=["preinscription"])
api_router.include_router(route_inscription.router, prefix="/inscription", tags=["inscription"])
api_router.include_router(route_besoins.router, prefix="/besoins", tags=["besoins"])
api_router.include_router(route_satisfaction.router, prefix="/satisfaction", tags=["satisfaction"])
api_router.include_router(route_evenement.router, prefix="/event", tags=["evenement"])
api_router.include_router(route_programme.router, prefix="/programmes", tags=["Programmes"])
api_router.include_router(route_emargement.router, prefix="/emargement", tags=["emargement"])

print("✅ Routes incluses")

app.include_router(api_router)
print("✅ Router principal inclus")



# ✅ Routes de base
@app.get("/", tags=["Root"],include_in_schema=False)
@app.head("/",include_in_schema=False)  # Autoriser HEAD sur "/"
def read_root(request: Request):
    print("\n🏠 Accès à la page d'accueil")
    result = request.session.pop("result", None)
    download_url = request.session.pop("download_url", None)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documentation": "/api-mca/v1/documentation",
        "url_process": "/api-mca/v1/process",
        "result": result,
        "download_url": download_url
    })

@app.get("/ping",include_in_schema=False)
async def ping():
    print("\n🏓 Ping reçu")
    return {"status": "ok"}

# ✅ Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    print("\n🌟 Événement de démarrage")

@app.on_event("shutdown")
async def shutdown_event():
    print("\n🌙 Événement d'arrêt")

# ✅ Lancement du serveur
if __name__ == "__main__":
    try:
        print("\n🚀 Démarrage du serveur...")
        port = int(os.environ.get("PORT", 8000))
        print(f"🌐 Serveur démarré sur http://localhost:{port}")
        asyncio.run(uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, reload_dirs=["app"]))
    except asyncio.CancelledError:
        print("\n❌ Interruption détectée, arrêt propre du serveur...")
    except Exception as e:
        print(f"\n💥 Erreur lors du démarrage du serveur: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        raise


