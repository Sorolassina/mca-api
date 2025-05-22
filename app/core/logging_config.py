import logging
import sys
from pathlib import Path

# Créer le dossier logs s'il n'existe pas
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configuration du logging
def setup_logging():
    # Créer le logger de l'application
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)  # Changé en DEBUG pour capturer plus de logs
    
    # Supprimer les handlers existants pour éviter les doublons
    logger.handlers = []
    
    # Créer les handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(
        filename=log_dir / "app.log",
        encoding='utf-8',
        mode='a'
    )
    
    # Définir les niveaux de log pour chaque handler
    console_handler.setLevel(logging.INFO)  # Console montre INFO et plus
    file_handler.setLevel(logging.DEBUG)    # Fichier montre tout
    
    # Créer le formatter avec plus de détails
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Ajouter les handlers au logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Configuration spécifique pour SQLAlchemy
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.INFO)
    sqlalchemy_logger.addHandler(file_handler)
    
    # Configuration pour les autres loggers importants
    for logger_name in ['uvicorn', 'fastapi', 'app.routes', 'app.services']:
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(logging.DEBUG)
        module_logger.addHandler(file_handler)
        module_logger.propagate = False
    
    # Désactiver la propagation vers le logger racine
    logger.propagate = False
    
    # Log de test pour vérifier que la configuration fonctionne
    logger.debug("Configuration du logging initialisée avec succès")
    
    return logger 