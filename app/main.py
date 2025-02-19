from fastapi import FastAPI
from app.routes import route_generate_pdf_from_html, route_qpv, route_siret_pappers
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Mon API PDF", description="Génération de PDF via FastAPI")
# Monter le dossier static pour que FastAPI puisse y accéder
app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "app/static")), name="static")

# Inclusion des routes
app.include_router(route_generate_pdf_from_html.router, prefix="/pdf", tags=["Génération de PDF à partir de HTML"])
app.include_router(route_siret_pappers.router, prefix="/api-pappers", tags=["siret"])
app.include_router(route_qpv.router, prefix="/qpv", tags=["qpv"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API de génération de PDF 🚀"}