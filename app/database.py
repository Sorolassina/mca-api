# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings
from app.models.models import Base
import os

# Déterminer le schéma à utiliser en fonction de l'environnement
SCHEMA_NAME = "public" if settings.ENVIRONNEMENT == "development" else "mca_api"

print(f"🔄 DATABASE_URL: {settings.DATABASE_URL}")
print(f"📚 Utilisation du schéma: {SCHEMA_NAME}")

DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Créer le moteur de base de données asynchrone
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Affiche les requêtes SQL dans les logs
    future=True,
    connect_args={
        "server_settings": {
            "search_path": SCHEMA_NAME  # Utiliser le schéma approprié selon l'environnement
        }
    }
)

# Créer une factory de sessions asynchrones
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Dépendance FastAPI pour obtenir une session DB
async def get_db():
    """
    Fournit une session de base de données pour chaque requête.
    S'assure que la session est fermée après utilisation.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Utilisation de text() pour la requête SQL textuelle
            await session.execute(text(f"SET search_path TO {SCHEMA_NAME}"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """
    Initialise la base de données en créant toutes les tables.
    À utiliser uniquement en développement.
    """
    print(f"🔄 Initialisation de la base de données dans le schéma {SCHEMA_NAME}...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Base de données initialisée avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {str(e)}")
        raise