from fastapi import FastAPI
from app.routes import route_generate_pdf_from_html, route_siret_pappers

app = FastAPI(title="Mon API PDF", description="Génération de PDF via FastAPI")

# Inclusion des routes
app.include_router(route_generate_pdf_from_html.router, prefix="/pdf", tags=["Génération de PDF à partir de HTML"])
app.include_router(route_siret_pappers.router, prefix="/api-pappers", tags=["SIRET"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API de génération de PDF 🚀"}