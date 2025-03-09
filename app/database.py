from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from app.config import DATABASE_URL

# Charger les variables d'environnement depuis .env
load_dotenv()

# Charger l'URL de la base de données depuis .env
DATABASE_URL = DATABASE_URL

# ✅ Création du moteur asynchrone
engine = create_async_engine(DATABASE_URL, echo=True)

# ✅ Création de la session asynchrone
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ✅ Déclaration de la base pour les modèles
Base = declarative_base()

# ✅ Fonction pour obtenir une session asynchrone
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
