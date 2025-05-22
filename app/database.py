# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Modifier l'URL de la base de données pour utiliser asyncpg
# Si votre DATABASE_URL est de la forme postgresql://user:pass@host:port/dbname
# Il faut la changer en postgresql+asyncpg://user:pass@host:port/dbname
DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Créer le moteur de base de données asynchrone
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Affiche les requêtes SQL dans les logs
    future=True
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
            yield session  # Fournit la session à la route
            await session.commit()  # Commit les changements si tout va bien
        except Exception:
            await session.rollback()  # Rollback en cas d'erreur
            raise
        finally:
            await session.close()  # Ferme toujours la session