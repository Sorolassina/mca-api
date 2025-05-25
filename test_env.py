import os
from dotenv import load_dotenv
from app.config import settings

def test_env_loading():
    print("\n=== Test de chargement des variables d'environnement ===")
    
    # 1. Lecture directe du fichier .env
    print("\n1. Contenu exact du fichier .env :")
    env_path = os.path.join(os.getcwd(), '.env')
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            print("=== Contenu du fichier .env ===")
            content = f.read()
            print(content)
            print("============================")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier .env: {e}")
    
    # 2. Test avec python-dotenv
    print("\n2. Valeurs chargées par python-dotenv :")
    load_dotenv(override=True)  # Force le rechargement
    for key in ['DB_USER', 'DB_HOST', 'DB_NAME', 'DB_PORT']:
        print(f"{key} (dotenv): {os.getenv(key)}")
    
    # 3. Test avec notre configuration
    print("\n3. Valeurs chargées par app.config.settings :")
    print(f"DB_USER (settings): {settings.DB_USER}")
    print(f"DB_HOST (settings): {settings.DB_HOST}")
    print(f"DB_NAME (settings): {settings.DB_NAME}")
    print(f"DB_PORT (settings): {settings.DB_PORT}")
    print(f"DATABASE_URL (settings): {settings.DATABASE_URL}")
    
    # 4. Vérification du chemin
    print("\n4. Informations sur le fichier .env :")
    print(f"Chemin absolu: {os.path.abspath(env_path)}")
    print(f"Le fichier existe: {os.path.exists(env_path)}")
    print(f"Taille du fichier: {os.path.getsize(env_path)} octets")

if __name__ == "__main__":
    test_env_loading() 