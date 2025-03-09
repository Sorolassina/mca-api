import sys
import os

# ✅ Ajoute le chemin de `app/` pour éviter l'import error
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from alembic import context
from app.models.model_user import Base  # ✅ Assure-toi que `Base` est bien défini dans `models.py`

import time

# 🔄 Essayer de récupérer DATABASE_URL plusieurs fois
MAX_RETRIES = 5
retry_count = 0

DATABASE_URL = None
while retry_count < MAX_RETRIES:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        print(f"✅ [DEBUG] DATABASE_URL récupérée après {retry_count + 1} essais.")
        break
    print(f"⏳ [ATTENTE] DATABASE_URL indisponible, tentative {retry_count + 1}/{MAX_RETRIES}...")
    time.sleep(3)
    retry_count += 1

if not DATABASE_URL:
    raise ValueError("❌ ERREUR : DATABASE_URL est toujours vide après plusieurs tentatives !")


DATABASE_URL_SYNC = DATABASE_URL.replace("asyncpg", "psycopg2")

# ✅ Création d'un moteur de connexion synchrone pour Alembic
engine = create_engine(DATABASE_URL_SYNC)

# ✅ Metadonnées pour les migrations (obligatoire pour `--autogenerate`)
target_metadata = Base.metadata

def run_migrations_offline():
    """Exécute les migrations en mode offline."""
    context.configure(url=DATABASE_URL_SYNC, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Exécute les migrations en mode online."""
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
