import psycopg2
from app.config import settings

def test_connection():
    try:
        # Construction de l'URL de connexion
        conn_string = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        print(f"🔄 Tentative de connexion à la base de données...")
        print(f"📝 URL de connexion (masquée): postgresql://{settings.DB_USER}:****@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        # Connexion à la base de données
        conn = psycopg2.connect(conn_string)
        
        # Test de connexion avec une requête simple
        with conn.cursor() as cur:
            cur.execute('SELECT version();')
            version = cur.fetchone()[0]
            print(f"✅ Connexion réussie !")
            print(f"📊 Version de PostgreSQL: {version}")
            
            # Test de création de schéma si nécessaire
            cur.execute('CREATE SCHEMA IF NOT EXISTS mca_api;')
            print("✅ Schéma 'mca_api' vérifié/créé")
        
        # Fermeture de la connexion
        conn.close()
        print("✅ Connexion fermée proprement")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        raise

if __name__ == "__main__":
    test_connection() 